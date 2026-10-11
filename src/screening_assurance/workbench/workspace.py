"""Local, file-based workspace for the Candidate Rediscovery Workbench.

Layout (default ./workspace, git-ignored)::

    sessions/<session-id>/
        session.json                 metadata, input hashes, retention deadline
        inputs/                      immutable copies of the validated inputs
        decisions.yaml               finding decisions (existing `decisions` contract)
        review-decisions.yaml        candidate decisions (`review_decisions` contract)
        runs/<run-id>/
            run.json                 run reference: input hashes, knowledge fingerprint, engine version, output hashes
            knowledge/               snapshot of the exact knowledge documents used
            decisions.yaml           decisions as applied to this run
            result.json              diagnostic result
            discovery.json           rediscovery result
        audit.jsonl                  attributable events; never candidate evidence or rationale text
    audit.jsonl                      workspace-level events (session creation, deletion)

The engine and knowledge pack remain authoritative; this module only orchestrates them.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import secrets
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from .. import ENGINE_VERSION
from ..contracts import ContractError, parse_text, validate_data
from ..engine import RequisitionBundle, diagnose, discover
from ..engine.discovery import ACTIONABLE
from ..knowledge import KnowledgeRegistry, load_pack
from ..report import render_changes, render_html, render_markdown
from ..report.discovery import review_rows

MAX_FILE_BYTES = 2 * 1024 * 1024
INPUT_KINDS = {
    # kind: (contract, filename, required)
    "requisition": ("requisition", "requisition.yaml", True),
    "policy": ("policy", "policy.yaml", True),
    "candidates": ("candidates", "candidates.yaml", False),
    "candidate_pool": ("candidate_pool", "candidate-pool.yaml", False),
    "outcomes": ("outcomes", "outcomes.yaml", False),
}
FINDING_DISPOSITIONS = {
    "unverified_necessity": ["confirmed_necessary", "reclassified_preferred", "requested_evidence", "deferred"],
    "candidate_review_opportunity": ["approved_candidate_review", "rejected", "requested_evidence", "deferred"],
    "unexplained_exclusions": ["accepted", "requested_evidence", "deferred"],
    "measured_impact": [],
}
DESIGN_DISPOSITIONS = ["accepted", "rejected", "deferred", "requested_evidence", "confirmed_necessary"]
CANDIDATE_DISPOSITIONS = ["review_in_ats", "request_more_information", "not_a_fit_for_this_role", "defer"]
EXPORTS = {
    "report.md": "text/markdown; charset=utf-8",
    "report.html": "text/html; charset=utf-8",
    "review-list.csv": "text/csv; charset=utf-8",
    "review-list.yaml": "application/yaml",
    "findings.json": "application/json",
    "discovery.json": "application/json",
    "decisions.yaml": "application/yaml",
    "review-decisions.yaml": "application/yaml",
    "changes.yaml": "application/yaml",
    "bundle.zip": "application/zip",
}


class WorkbenchError(ValueError):
    """A user-facing error (bad input, unknown id, disallowed action)."""

    def __init__(self, message: str, details: list[str] | None = None, status: int = 400):
        super().__init__(message)
        self.details = details or []
        self.status = status


def allowed_dispositions(check: str) -> list[str]:
    return FINDING_DISPOSITIONS.get(check, DESIGN_DISPOSITIONS)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _safe_id(value: str, prefix: str) -> str:
    if not isinstance(value, str) or not value.startswith(prefix) or not all(ch.isalnum() or ch in "-_" for ch in value) or len(value) > 64:
        raise WorkbenchError(f"invalid identifier: {value!r}", status=404)
    return value


@dataclass
class ValidatedInputs:
    texts: dict[str, str]
    data: dict[str, Any]
    report: list[dict[str, Any]]
    ok: bool


class Workspace:
    def __init__(self, root: str | Path, knowledge_root: str | Path = "knowledge",
                 examples_root: str | Path = "examples", evals_root: str | Path = "evals"):
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.registry = KnowledgeRegistry(knowledge_root)
        self.examples_root = Path(examples_root)
        self.evals_root = Path(evals_root)

    # ------------------------------------------------------------------ audit
    def _audit(self, event: str, session_id: str | None = None, **fields: Any) -> None:
        line = json.dumps({"at": _now().isoformat(), "event": event, "session": session_id, **fields}, default=str)
        path = (self.sessions_dir / session_id / "audit.jsonl") if session_id and (self.sessions_dir / session_id).exists() \
            else self.root / "audit.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        if path != self.root / "audit.jsonl" and event in ("session_created",):
            with (self.root / "audit.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    # ------------------------------------------------------------------ knowledge
    def knowledge_options(self) -> list[dict[str, Any]]:
        out = []
        dep = self.registry.deployments()["environments"]
        for env, ver in sorted(dep.items()):
            try:
                p = self.registry.load(f"env:{env}")
                out.append({"spec": f"env:{env}", "label": f"{env} ({ver})", "fingerprint": p.fingerprint, "status": p.manifest["status"]})
            except Exception:  # noqa: BLE001 - a broken environment should not break the workbench
                continue
        for ver in reversed(self.registry.releases()):
            p = self.registry.load(f"release:{ver}")
            out.append({"spec": f"release:{ver}", "label": f"release {ver}", "fingerprint": p.fingerprint, "status": "released"})
        try:
            p = self.registry.load("pack")
            out.append({"spec": "pack", "label": f"working pack ({p.version}, {p.manifest['status']})",
                        "fingerprint": p.fingerprint, "status": p.manifest["status"]})
        except ContractError as exc:
            out.append({"spec": "pack", "label": "working pack (invalid)", "fingerprint": None, "status": "invalid",
                        "errors": exc.errors[:5]})
        return out

    # ------------------------------------------------------------------ examples
    def examples(self) -> list[dict[str, Any]]:
        out = []
        for req_path in sorted(self.examples_root.rglob("requisition.yaml")):
            d = req_path.parent
            try:
                data = parse_text(req_path.read_text(encoding="utf-8"), str(req_path))
            except ContractError:
                continue
            files = [k for k, (_, fn, _) in INPUT_KINDS.items() if (d / fn).exists() and k not in ("requisition", "policy")]
            out.append({"id": d.name, "title": data.get("title"), "job_family": data.get("job_family"), "files": files,
                        "screening_configuration": (data.get("inputs_received") or {}).get("screening_configuration")})
        return out

    def _example_texts(self, example_id: str, include_outcomes: bool) -> dict[str, str]:
        matches = [p.parent for p in self.examples_root.rglob("requisition.yaml") if p.parent.name == example_id]
        if not matches:
            raise WorkbenchError(f"unknown example {example_id!r}", status=404)
        d = matches[0]
        texts: dict[str, str] = {}
        for kind, (_, fn, _) in INPUT_KINDS.items():
            path = d / fn
            if kind == "policy" and not path.exists():
                for parent in (d.parent, d.parent.parent, d.parent.parent.parent):
                    if (parent / "policy.yaml").exists():
                        path = parent / "policy.yaml"
                        break
            if kind == "outcomes" and not include_outcomes:
                continue
            if path.exists():
                texts[kind] = path.read_text(encoding="utf-8")
        return texts

    # ------------------------------------------------------------------ validation
    def validate_inputs(self, texts: dict[str, str]) -> ValidatedInputs:
        report: list[dict[str, Any]] = []
        data: dict[str, Any] = {}
        unknown = sorted(set(texts) - set(INPUT_KINDS))
        if unknown:
            raise WorkbenchError(f"unsupported input kind(s): {', '.join(unknown)}")
        for kind, (contract, _, required) in INPUT_KINDS.items():
            text = texts.get(kind)
            if text is None or text == "":
                report.append({"kind": kind, "status": "missing" if required else "not_supplied", "required": required, "errors": []})
                continue
            if not isinstance(text, str):
                report.append({"kind": kind, "status": "invalid", "required": required, "errors": ["file content must be text"]})
                continue
            size = len(text.encode("utf-8"))
            if size > MAX_FILE_BYTES:
                report.append({"kind": kind, "status": "invalid", "required": required,
                               "errors": [f"file is {size:,} bytes; the limit is {MAX_FILE_BYTES:,}"]})
                continue
            try:
                parsed = parse_text(text, kind)
                validate_data(contract, parsed, kind)
            except ContractError as exc:
                report.append({"kind": kind, "status": "invalid", "required": required,
                               "errors": [e[:300] for e in exc.errors[:20]]})
                continue
            data[kind] = parsed
            report.append({"kind": kind, "status": "valid", "required": required, "errors": [], "sha256": _sha(text), "bytes": size})
        # Cross-file consistency.
        req = data.get("requisition")
        if req:
            for kind in ("candidates", "outcomes"):
                if kind in data and data[kind]["requisition_id"] != req["id"]:
                    _fail(report, kind, f"is for requisition {data[kind]['requisition_id']}, not {req['id']}")
            if "policy" in data and data["policy"]["employer_id"] != req["employer_id"]:
                _fail(report, "policy", f"is for employer {data['policy']['employer_id']}, not {req['employer_id']}")
            claimed = req["inputs_received"]["candidate_evidence"]
            if claimed == "not_supplied" and ("candidates" in data):
                _note(report, "candidates", "requisition says candidate evidence was not supplied, but a candidates file was provided")
        ok = all(r["status"] in ("valid", "not_supplied") for r in report)
        for kind in list(data):
            if next(r for r in report if r["kind"] == kind)["status"] != "valid":
                data.pop(kind)
        return ValidatedInputs(texts={k: v for k, v in texts.items() if k in data}, data=data, report=report, ok=ok)

    @staticmethod
    def input_summary(data: dict[str, Any]) -> dict[str, Any]:
        """Distinguish verified configuration, recruiter documentation, and missing data."""
        req = data.get("requisition") or {}
        ir = req.get("inputs_received") or {}
        cfg = ir.get("screening_configuration")
        cfg_label = {
            "ats_export_verified": "Supplied ATS configuration (exported from the ATS)",
            "ats_api_verified": "Supplied ATS configuration (read from the ATS)",
            "recruiter_documentation": "Recruiter documentation — not verified ATS configuration",
            "not_supplied": "Missing — no screening configuration supplied",
        }.get(cfg, "Unknown")
        pool = data.get("candidate_pool")
        return {
            "job_description": ir.get("job_description"),
            "screening_configuration": cfg,
            "screening_configuration_label": cfg_label,
            "screening_rules": len(req.get("screening_rules", [])),
            "candidate_evidence": ir.get("candidate_evidence"),
            "current_applicants": len((data.get("candidates") or {}).get("candidates", [])) if data.get("candidates") else None,
            "pool": None if not pool else {
                "pool_id": pool["pool_id"], "source_system": pool["source_system"], "exported_at": pool["exported_at"],
                "records": len(pool["candidates"]), "permitted_uses": pool["authorization"]["permitted_uses"],
                "retention_days": pool["authorization"]["retention_days"], "deletion": pool["authorization"]["deletion"],
                "max_evidence_age_days": pool.get("max_evidence_age_days", 730),
            },
            "outcomes": bool(data.get("outcomes")),
            "notes": ir.get("notes"),
        }

    # ------------------------------------------------------------------ sessions
    def create_session(self, texts: dict[str, str], *, source: str, actor: str) -> dict[str, Any]:
        v = self.validate_inputs(texts)
        if not v.ok:
            raise WorkbenchError("inputs failed validation", [f"{r['kind']}: {e}" for r in v.report for e in r["errors"]]
                                 + [f"{r['kind']}: required" for r in v.report if r["status"] == "missing"])
        sid = "S-" + secrets.token_hex(5)
        d = self.sessions_dir / sid
        (d / "inputs").mkdir(parents=True)
        inputs = {}
        for kind, text in v.texts.items():
            fn = INPUT_KINDS[kind][1]
            (d / "inputs" / fn).write_text(text, encoding="utf-8")
            inputs[kind] = {"file": fn, "sha256": _sha(text), "bytes": len(text.encode("utf-8"))}
        retention = [v.data[k]["authorization"]["retention_days"] for k in ("candidates", "candidate_pool") if k in v.data]
        created = _now()
        deletion = (v.data.get("candidate_pool") or {}).get("authorization", {}).get("deletion", "delete_candidate_data")
        meta = {
            "id": sid,
            "created_at": created.isoformat(),
            "created_by": actor,
            "source": source,
            "requisition_id": v.data["requisition"]["id"],
            "title": v.data["requisition"]["title"],
            "inputs": inputs,
            "summary": self.input_summary(v.data),
            "retention": {
                "days": min(retention) if retention else None,
                "delete_after": (created + timedelta(days=min(retention))).isoformat() if retention else None,
                "deletion": deletion,
                "basis": "shortest retention_days among supplied candidate inputs, counted from import into this workspace",
            },
            "candidate_data_deleted": False,
        }
        (d / "session.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self._audit("session_created", sid, actor=actor, source=source, requisition=meta["requisition_id"],
                    inputs={k: x["sha256"][:12] for k, x in inputs.items()})
        return meta

    def create_session_from_example(self, example_id: str, *, actor: str, include_outcomes: bool = True) -> dict[str, Any]:
        return self.create_session(self._example_texts(example_id, include_outcomes), source=f"example:{example_id}", actor=actor)

    def _session_dir(self, sid: str) -> Path:
        d = self.sessions_dir / _safe_id(sid, "S-")
        if not (d / "session.json").exists():
            raise WorkbenchError("session not found (it may have been deleted under its retention rule)", status=404)
        return d

    def session(self, sid: str) -> dict[str, Any]:
        d = self._session_dir(sid)
        meta = json.loads((d / "session.json").read_text())
        meta["runs"] = self.runs(sid)
        meta["decisions"] = self.finding_decisions(sid).get("decisions", [])
        meta["review_decisions"] = self.review_decisions(sid).get("decisions", [])
        if not meta.get("candidate_data_deleted"):
            data = self._inputs(sid)
            req = data["requisition"]
            meta["requisition"] = {"id": req["id"], "title": req["title"], "job_family": req["job_family"],
                                   "description": req["description"], "objectives": req.get("objectives", []),
                                   "requirements": req["requirements"], "screening_rules": req["screening_rules"]}
            pol = data["policy"]
            meta["policy"] = {"employer_name": pol["employer_name"], "policy_version": pol["policy_version"],
                              "non_negotiable": pol.get("non_negotiable", []),
                              "accepted_equivalencies": pol.get("accepted_equivalencies", []),
                              "rejected_equivalencies": pol.get("rejected_equivalencies", [])}
        return meta

    def sessions(self) -> list[dict[str, Any]]:
        out = []
        for d in sorted(self.sessions_dir.glob("S-*")):
            if (d / "session.json").exists():
                m = json.loads((d / "session.json").read_text())
                out.append({k: m.get(k) for k in ("id", "title", "requisition_id", "created_at", "source", "retention", "candidate_data_deleted")})
        return out

    def _inputs(self, sid: str) -> dict[str, Any]:
        d = self._session_dir(sid)
        meta = json.loads((d / "session.json").read_text())
        data = {}
        for kind, info in meta["inputs"].items():
            path = d / "inputs" / info["file"]
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            if _sha(text) != info["sha256"]:
                raise WorkbenchError(f"input {info['file']} was modified after import; create a new session", status=409)
            data[kind] = validate_data(INPUT_KINDS[kind][0], parse_text(text, kind), kind)
        return data

    def delete_session(self, sid: str, *, actor: str, reason: str) -> None:
        d = self._session_dir(sid)
        shutil.rmtree(d)
        self._audit("session_deleted", None, deleted_session=sid, actor=actor, reason=reason)

    def purge_expired(self, now: datetime | None = None) -> list[str]:
        """Apply retention: remove candidate-level data once a session's retention period ends."""
        now = now or _now()
        purged = []
        for d in sorted(self.sessions_dir.glob("S-*")):
            p = d / "session.json"
            if not p.exists():
                continue
            meta = json.loads(p.read_text())
            when = (meta.get("retention") or {}).get("delete_after")
            if not when or meta.get("candidate_data_deleted") or datetime.fromisoformat(when) > now:
                continue
            if meta["retention"].get("deletion") == "delete_workspace_session":
                shutil.rmtree(d)
                self._audit("session_deleted", None, deleted_session=meta["id"], actor="retention", reason="retention period ended")
            else:
                self._delete_candidate_data(d, meta)
                self._audit("candidate_data_deleted", meta["id"], actor="retention", reason="retention period ended")
            purged.append(meta["id"])
        return purged

    def _delete_candidate_data(self, d: Path, meta: dict[str, Any]) -> None:
        for kind in ("candidates", "candidate_pool", "outcomes"):
            info = meta["inputs"].pop(kind, None)
            if info and (d / "inputs" / info["file"]).exists():
                (d / "inputs" / info["file"]).unlink()
        for sub in ("runs",):
            if (d / sub).exists():
                shutil.rmtree(d / sub)
        for fn in ("review-decisions.yaml",):
            if (d / fn).exists():
                (d / fn).unlink()
        meta["candidate_data_deleted"] = True
        (d / "session.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ decisions
    def finding_decisions(self, sid: str) -> dict[str, Any]:
        p = self._session_dir(sid) / "decisions.yaml"
        meta = json.loads((p.parent / "session.json").read_text())
        if not p.exists():
            return {"requisition_id": meta["requisition_id"], "decisions": []}
        return validate_data("decisions", parse_text(p.read_text(encoding="utf-8")), "decisions.yaml")

    def review_decisions(self, sid: str) -> dict[str, Any]:
        p = self._session_dir(sid) / "review-decisions.yaml"
        meta = json.loads((p.parent / "session.json").read_text())
        if not p.exists():
            return {"requisition_id": meta["requisition_id"], "decisions": []}
        return validate_data("review_decisions", parse_text(p.read_text(encoding="utf-8")), "review-decisions.yaml")

    def record_finding_decision(self, sid: str, run_id: str, finding_id: str, disposition: str,
                                rationale: str, actor: str) -> dict[str, Any]:
        run = self.load_run(sid, run_id)
        f = next((x for x in run["result"]["findings"] if x["id"] == finding_id), None)
        if not f:
            raise WorkbenchError(f"finding {finding_id} is not part of run {run_id}", status=404)
        allowed = allowed_dispositions(f["check"])
        if disposition not in allowed:
            raise WorkbenchError(f"'{disposition}' is not a valid decision for this finding; allowed: {', '.join(allowed) or 'none'}")
        rationale, actor = _require_text(rationale, "rationale"), _require_text(actor, "reviewer")
        doc = self.finding_decisions(sid)
        doc["decisions"] = [d for d in doc["decisions"] if d["finding_id"] != finding_id]
        entry = {"finding_id": finding_id, "disposition": disposition, "rationale": rationale,
                 "decided_by": actor, "decided_at": _now().isoformat()}
        doc["decisions"].append(entry)
        validate_data("decisions", doc, "decisions.yaml")
        (self._session_dir(sid) / "decisions.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        self._audit("finding_decision", sid, actor=actor, finding=finding_id, disposition=disposition, run=run_id,
                    rationale_sha256=_sha(rationale)[:16])
        return entry

    def record_candidate_decision(self, sid: str, run_id: str, candidate_id: str, disposition: str, rationale: str,
                                  actor: str, review_minutes: float | None = None) -> dict[str, Any]:
        run = self.load_run(sid, run_id)
        e = next((x for x in run["discovery"]["entries"] if x["candidate_id"] == candidate_id), None)
        if not e:
            raise WorkbenchError(f"candidate {candidate_id} is not part of run {run_id}", status=404)
        if e["group"] not in ACTIONABLE:
            raise WorkbenchError(f"candidate {candidate_id} is in group '{e['group']}' and is not available for review decisions")
        if disposition not in CANDIDATE_DISPOSITIONS:
            raise WorkbenchError(f"'{disposition}' is not a valid candidate decision; allowed: {', '.join(CANDIDATE_DISPOSITIONS)}")
        rationale, actor = _require_text(rationale, "rationale"), _require_text(actor, "reviewer")
        doc = self.review_decisions(sid)
        doc["decisions"] = [d for d in doc["decisions"] if d["candidate_id"] != candidate_id]
        entry = {"candidate_id": candidate_id, "disposition": disposition, "rationale": rationale, "decided_by": actor,
                 "decided_at": _now().isoformat(), "run_id": run_id, "knowledge": run["run"]["knowledge"]["fingerprint"]}
        if review_minutes not in (None, ""):
            try:
                entry["review_minutes"] = float(review_minutes)
            except (TypeError, ValueError):
                raise WorkbenchError("review minutes must be a number") from None
        doc["decisions"].append(entry)
        validate_data("review_decisions", doc, "review-decisions.yaml")
        (self._session_dir(sid) / "review-decisions.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
        self._audit("candidate_decision", sid, actor=actor, candidate=candidate_id, disposition=disposition, run=run_id,
                    rationale_sha256=_sha(rationale)[:16])
        return entry

    # ------------------------------------------------------------------ runs
    def runs(self, sid: str) -> list[dict[str, Any]]:
        d = self._session_dir(sid) / "runs"
        if not d.exists():
            return []
        out = [json.loads((r / "run.json").read_text()) for r in sorted(d.glob("R-*")) if (r / "run.json").exists()]
        return sorted(out, key=lambda r: r["run_at"])

    def run(self, sid: str, knowledge_spec: str, *, actor: str) -> dict[str, Any]:
        d = self._session_dir(sid)
        meta = json.loads((d / "session.json").read_text())
        if meta.get("candidate_data_deleted"):
            raise WorkbenchError("candidate data for this session was deleted under its retention rule; create a new session")
        actor = _require_text(actor, "reviewer")
        try:
            src = self.registry.resolve(knowledge_spec)
            load_pack(src)
        except (ContractError, FileNotFoundError) as exc:
            raise WorkbenchError(f"knowledge '{knowledge_spec}' cannot be used: {exc}"[:400]) from None
        run_at = _now()
        run_id = f"R-{run_at.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(2)}"
        rd = d / "runs" / run_id
        (rd / "knowledge").mkdir(parents=True)
        manifest = yaml.safe_load((src / "manifest.yaml").read_text())
        shutil.copy2(src / "manifest.yaml", rd / "knowledge" / "manifest.yaml")
        for rel in manifest["documents"].values():
            shutil.copy2(src / rel, rd / "knowledge" / Path(rel).name)
        if any(Path(rel).name != rel for rel in manifest["documents"].values()):
            m = dict(manifest)
            m["documents"] = {k: Path(v).name for k, v in manifest["documents"].items()}
            (rd / "knowledge" / "manifest.yaml").write_text(yaml.safe_dump(m, sort_keys=False))
        for name, loader in (("decisions.yaml", self.finding_decisions), ("review-decisions.yaml", self.review_decisions)):
            (rd / name).write_text(yaml.safe_dump(loader(sid), sort_keys=False, allow_unicode=True), encoding="utf-8")
        run = {
            "run_id": run_id,
            "session_id": sid,
            "requisition_id": meta["requisition_id"],
            "run_at": run_at.isoformat(),
            "as_of": run_at.date().isoformat(),
            "run_by": actor,
            "engine_version": ENGINE_VERSION,
            "knowledge": {"spec": knowledge_spec, "fingerprint": None, "version": manifest["version"],
                          "status": manifest["status"], "source": str(src)},
            "inputs": {k: v["sha256"] for k, v in meta["inputs"].items()},
            "decisions_sha256": _sha((rd / "decisions.yaml").read_text(encoding="utf-8")),
            "review_decisions_sha256": _sha((rd / "review-decisions.yaml").read_text(encoding="utf-8")),
        }
        result, discovery = self._compute(sid, rd, run)
        run["knowledge"]["fingerprint"] = result["knowledge"]["fingerprint"]
        run["outputs"] = {"result_sha256": _sha(_canonical(result)), "discovery_sha256": _sha(_canonical(discovery))}
        run["summary"] = {**result["summary"], "discovery": discovery["counts"]}
        run["carried_over"] = self._carry_over(sid, result, discovery)
        (rd / "result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        (rd / "discovery.json").write_text(json.dumps(discovery, indent=2, default=str), encoding="utf-8")
        (rd / "run.json").write_text(json.dumps(run, indent=2), encoding="utf-8")
        self._audit("run", sid, actor=actor, run=run_id, knowledge=run["knowledge"]["fingerprint"],
                    result=run["outputs"]["result_sha256"][:16])
        return run

    def _compute(self, sid: str, rd: Path, run: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        data = self._inputs(sid)
        for kind, sha in run["inputs"].items():
            if kind in INPUT_KINDS and kind not in data:
                raise WorkbenchError(f"input {kind} is no longer available (deleted under retention)", status=409)
        pack = load_pack(rd / "knowledge")
        decisions = validate_data("decisions", parse_text((rd / "decisions.yaml").read_text(encoding="utf-8")), "decisions")
        bundle = RequisitionBundle(path=None, requisition=data["requisition"], policy=data["policy"],
                                   candidates=data.get("candidates"), decisions=decisions,
                                   outcomes=data.get("outcomes"), pool=data.get("candidate_pool"))
        diag = diagnose(bundle, pack, run_at=run["run_at"])
        disc = discover(bundle, pack, diag, pool=data.get("candidate_pool"), as_of=run["as_of"])
        result = diag.as_dict()
        result["knowledge"]["path"] = f"runs/{run['run_id']}/knowledge"
        result["knowledge"]["spec"] = run["knowledge"]["spec"]
        for f in result["findings"]:
            f["allowed_dispositions"] = allowed_dispositions(f["check"])
        return result, disc.as_dict()

    def _carry_over(self, sid: str, result: dict[str, Any], discovery: dict[str, Any]) -> dict[str, Any]:
        fids = {f["id"] for f in result["findings"]}
        fd = self.finding_decisions(sid)["decisions"]
        actionable = {e["candidate_id"] for e in discovery["entries"] if e["group"] in ACTIONABLE}
        cd = self.review_decisions(sid)["decisions"]
        return {
            "finding_decisions_applied": sorted(d["finding_id"] for d in fd if d["finding_id"] in fids),
            "finding_decisions_stale": sorted(d["finding_id"] for d in fd if d["finding_id"] not in fids),
            "candidate_decisions_applied": sorted(d["candidate_id"] for d in cd if d["candidate_id"] in actionable),
            "candidate_decisions_stale": sorted(d["candidate_id"] for d in cd if d["candidate_id"] not in actionable),
        }

    def load_run(self, sid: str, run_id: str) -> dict[str, Any]:
        rd = self._session_dir(sid) / "runs" / _safe_id(run_id, "R-")
        if not (rd / "run.json").exists():
            raise WorkbenchError("run not found", status=404)
        return {
            "run": json.loads((rd / "run.json").read_text()),
            "result": json.loads((rd / "result.json").read_text()),
            "discovery": json.loads((rd / "discovery.json").read_text()),
        }

    def verify_run(self, sid: str, run_id: str, *, actor: str = "workbench") -> dict[str, Any]:
        """Re-run from the run's own input hashes, knowledge snapshot and decision snapshot; compare outputs."""
        rd = self._session_dir(sid) / "runs" / _safe_id(run_id, "R-")
        stored = self.load_run(sid, run_id)
        run = stored["run"]
        checks = []
        meta = json.loads((self._session_dir(sid) / "session.json").read_text())
        for kind, sha in run["inputs"].items():
            cur = meta["inputs"].get(kind, {}).get("sha256")
            checks.append({"check": f"input {kind} unchanged", "ok": cur == sha})
        snap = load_pack(rd / "knowledge")
        checks.append({"check": "knowledge snapshot matches recorded fingerprint",
                       "ok": snap.fingerprint == run["knowledge"]["fingerprint"], "detail": snap.fingerprint})
        checks.append({"check": "decision snapshot unchanged",
                       "ok": _sha((rd / "decisions.yaml").read_text(encoding="utf-8")) == run["decisions_sha256"]})
        try:
            result, discovery = self._compute(sid, rd, run)
            checks.append({"check": "diagnostic result reproduced", "ok": _sha(_canonical(result)) == run["outputs"]["result_sha256"]})
            checks.append({"check": "discovery result reproduced", "ok": _sha(_canonical(discovery)) == run["outputs"]["discovery_sha256"]})
        except WorkbenchError as exc:
            checks.append({"check": "re-run", "ok": False, "detail": str(exc)})
        ok = all(c["ok"] for c in checks)
        self._audit("verify_run", sid, actor=actor, run=run_id, reproduced=ok)
        return {"run_id": run_id, "reproduced": ok, "checks": checks}

    # ------------------------------------------------------------------ exports
    def export(self, sid: str, run_id: str, name: str, *, actor: str = "workbench") -> tuple[bytes, str, str]:
        if name not in EXPORTS:
            raise WorkbenchError(f"unknown export {name!r}", status=404)
        stored = self.load_run(sid, run_id)
        result, discovery, run = stored["result"], stored["discovery"], stored["run"]
        rd = self._session_dir(sid) / "runs" / run_id
        review = self.review_decisions(sid)
        rows = review_rows(discovery, review, run_id)
        stem = f"{run['requisition_id']}_{run_id}"
        if name == "report.md":
            body = render_markdown(result, discovery, review)
            body = _provenance_header(run) + body
        elif name == "report.html":
            body = render_html(result, discovery, review)
        elif name == "review-list.csv":
            buf = io.StringIO()
            fields = list(rows[0].keys()) if rows else ["candidate_id"]
            w = csv.DictWriter(buf, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: _csv_safe(v) for k, v in r.items()})
            body = buf.getvalue()
        elif name == "review-list.yaml":
            body = yaml.safe_dump({"requisition_id": run["requisition_id"], "run_id": run_id,
                                   "knowledge": run["knowledge"]["fingerprint"], "label": "Candidates for human review; not a qualification decision.",
                                   "candidates": rows}, sort_keys=False, allow_unicode=True)
        elif name == "findings.json":
            body = json.dumps(result, indent=2, default=str)
        elif name == "discovery.json":
            body = json.dumps(discovery, indent=2, default=str)
        elif name == "decisions.yaml":
            body = yaml.safe_dump(self.finding_decisions(sid), sort_keys=False, allow_unicode=True)
        elif name == "review-decisions.yaml":
            body = yaml.safe_dump(review, sort_keys=False, allow_unicode=True)
        elif name == "changes.yaml":
            body = yaml.safe_dump(render_changes(result), sort_keys=False, allow_unicode=True)
        else:  # bundle.zip
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                manifest = {"run": run, "files": {}}
                for part in [n for n in EXPORTS if n != "bundle.zip"]:
                    data, _, _ = self.export(sid, run_id, part, actor=actor)
                    z.writestr(part, data)
                    manifest["files"][part] = _sha(data)
                for f in sorted((rd / "knowledge").iterdir()):
                    z.write(f, f"knowledge/{f.name}")
                z.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
            self._audit("export", sid, actor=actor, run=run_id, export=name)
            return buf.getvalue(), EXPORTS[name], f"{stem}.zip"
        self._audit("export", sid, actor=actor, run=run_id, export=name)
        return body.encode("utf-8"), EXPORTS[name], f"{stem}_{name}"

    # ------------------------------------------------------------------ evaluation
    def evaluate(self, knowledge_spec: str) -> dict[str, Any]:
        from ..evals import render_suite_markdown, run_suite
        cases = self.evals_root / "cases"
        if not cases.exists():
            raise WorkbenchError("evaluation cases are not available in this installation", status=404)
        th = yaml.safe_load((self.evals_root / "thresholds.yaml").read_text()) if (self.evals_root / "thresholds.yaml").exists() else None
        suite = run_suite(cases, self.registry.load(knowledge_spec), th)
        return {"passed": suite["passed"], "failures": suite["failures"], "knowledge": suite["knowledge"],
                "markdown": render_suite_markdown(suite)}

    def compare(self, baseline: str, candidate: str) -> dict[str, Any]:
        from ..evals import compare_suites, render_compare_markdown, run_suite
        from ..knowledge import diff_packs
        from ..knowledge.diff import format_diff
        cases = self.evals_root / "cases"
        if not cases.exists():
            raise WorkbenchError("evaluation cases are not available in this installation", status=404)
        th = yaml.safe_load((self.evals_root / "thresholds.yaml").read_text()) if (self.evals_root / "thresholds.yaml").exists() else None
        b, c = self.registry.load(baseline), self.registry.load(candidate)
        cmp = compare_suites(run_suite(cases, b, th), run_suite(cases, c, th))
        md = render_compare_markdown(cmp) + "\n## Knowledge records changed\n\n```\n" + format_diff(diff_packs(b, c)) + "\n```\n"
        return {"passed": cmp["passed"], "regressions": cmp["regressions"], "baseline": b.fingerprint,
                "candidate": c.fingerprint, "markdown": md}


def _provenance_header(run: dict[str, Any]) -> str:
    inputs = ", ".join(f"{k} `{v[:12]}`" for k, v in run["inputs"].items())
    return (f"<!-- run {run['run_id']} -->\n> Run `{run['run_id']}` at {run['run_at']} by {run['run_by']} · knowledge "
            f"`{run['knowledge']['fingerprint']}` ({run['knowledge']['spec']}) · engine {run['engine_version']} · "
            f"inputs (sha256): {inputs}\n\n")


def _csv_safe(v: Any) -> Any:
    """Neutralize spreadsheet formula injection in exported CSV cells."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def _require_text(value: Any, name: str, limit: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkbenchError(f"{name} is required")
    value = value.strip()
    if len(value) > limit:
        raise WorkbenchError(f"{name} is longer than {limit} characters")
    return value


def _fail(report: list[dict[str, Any]], kind: str, msg: str) -> None:
    r = next(x for x in report if x["kind"] == kind)
    r["status"] = "invalid"
    r["errors"].append(msg)


def _note(report: list[dict[str, Any]], kind: str, msg: str) -> None:
    r = next(x for x in report if x["kind"] == kind)
    r.setdefault("notes", []).append(msg)

