"""Loopback-only HTTP server for the Candidate Rediscovery Workbench (standard library only).

Safety boundaries:
  * binds to 127.0.0.1 by default; refuses non-loopback hosts unless explicitly allowed
  * every API call needs a per-launch token sent in the X-SA-Token header (blocks cross-site requests)
  * Host header must be a loopback name (blocks DNS rebinding)
  * JSON bodies only, size-limited; uploads are validated against the data contracts
  * strict Content-Security-Policy; the UI renders with textContent, never innerHTML of data
  * request logs contain method, path and status only — never bodies or candidate evidence
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import re
import secrets
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any
from urllib.parse import unquote, urlparse

from .. import ENGINE_VERSION
from ..contracts import ContractError
from .workspace import CANDIDATE_DISPOSITIONS, EXPORTS, INPUT_KINDS, MAX_FILE_BYTES, Workspace, WorkbenchError

MAX_BODY_BYTES = len(INPUT_KINDS) * MAX_FILE_BYTES + 64 * 1024
LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1"}
STATIC = {"app.js": "text/javascript; charset=utf-8", "app.css": "text/css; charset=utf-8"}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def _static(name: str) -> bytes:
    return resources.files("screening_assurance.workbench.static").joinpath(name).read_bytes()


def is_loopback(host: str) -> bool:
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], workspace: Workspace, *, token: str | None = None, quiet: bool = False):
        self.workspace = workspace
        self.token = token or secrets.token_urlsafe(24)
        self.quiet = quiet
        self.lock = threading.Lock()  # serialize writes to the workspace
        super().__init__(address, Handler)

    @property
    def url(self) -> str:
        host, port = self.server_address[:2]
        host = "127.0.0.1" if host in ("127.0.0.1", "0.0.0.0") else host
        return f"http://{host}:{port}/"


class Handler(BaseHTTPRequestHandler):
    server: WorkbenchServer
    server_version = "ScreeningAssurance"
    sys_version = ""

    # ---------------------------------------------------------------- plumbing
    def log_message(self, fmt: str, *args: Any) -> None:  # never log bodies or query strings
        if not self.server.quiet:
            path = urlparse(self.path).path
            sys.stderr.write(f"{self.command} {path} {args[1] if len(args) > 1 else ''}\n")

    def _headers(self, status: int, ctype: str, length: int, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", CSP)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def _json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _error(self, status: int, message: str, details: list[str] | None = None) -> None:
        self._json(status, {"error": message[:500], "details": [d[:300] for d in (details or [])][:50]})

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").strip()
        if host.startswith("["):
            name = host[1:host.find("]")] if "]" in host else host
        else:
            name = host.rsplit(":", 1)[0] if ":" in host else host
        return is_loopback(name) or name == self.server.server_address[0]

    def _token_ok(self) -> bool:
        return hmac.compare_digest(self.headers.get("X-SA-Token", ""), self.server.token)

    def _body(self) -> dict[str, Any]:
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            raise WorkbenchError("requests must be JSON (Content-Type: application/json)", status=415)
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise WorkbenchError("invalid Content-Length") from None
        if length > MAX_BODY_BYTES:
            raise WorkbenchError(f"request is larger than {MAX_BODY_BYTES:,} bytes", status=413)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise WorkbenchError("request body is not valid JSON") from None
        if not isinstance(data, dict):
            raise WorkbenchError("request body must be a JSON object")
        return data

    def _dispatch(self, method: str) -> None:
        if not self._host_ok():
            return self._error(HTTPStatus.FORBIDDEN, "host not allowed")
        path = urlparse(self.path).path
        try:
            if method == "GET" and path in ("/", "/index.html"):
                return self._index()
            if method == "GET" and path.startswith("/static/"):
                name = path.rsplit("/", 1)[-1]
                if name not in STATIC:
                    return self._error(HTTPStatus.NOT_FOUND, "not found")
                body = _static(name)
                self._headers(200, STATIC[name], len(body))
                return self.wfile.write(body)
            if not path.startswith("/api/"):
                return self._error(HTTPStatus.NOT_FOUND, "not found")
            if not self._token_ok():
                return self._error(HTTPStatus.FORBIDDEN, "missing or invalid workbench token")
            self.server.workspace.purge_expired()
            return self._api(method, [unquote(p) for p in path[len("/api/"):].split("/") if p])
        except WorkbenchError as exc:
            return self._error(exc.status, str(exc), exc.details)
        except ContractError as exc:
            return self._error(HTTPStatus.BAD_REQUEST, "input failed contract validation", exc.errors)
        except Exception as exc:  # noqa: BLE001 - do not leak internals or data in error bodies
            if not self.server.quiet:
                sys.stderr.write(f"internal error: {type(exc).__name__}\n")
            return self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"internal error ({type(exc).__name__})")

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def _index(self) -> None:
        html = _static("index.html").decode("utf-8").replace("__SA_TOKEN__", self.server.token)
        body = html.encode("utf-8")
        self._headers(200, "text/html; charset=utf-8", len(body))
        self.wfile.write(body)

    # ---------------------------------------------------------------- API
    def _api(self, method: str, parts: list[str]) -> None:
        ws = self.server.workspace
        if parts == ["state"] and method == "GET":
            return self._json(200, {
                "engine_version": ENGINE_VERSION,
                "knowledge": ws.knowledge_options(),
                "examples": ws.examples(),
                "sessions": ws.sessions(),
                "candidate_dispositions": CANDIDATE_DISPOSITIONS,
                "input_kinds": {k: {"contract": c, "file": f, "required": r} for k, (c, f, r) in INPUT_KINDS.items()},
                "max_file_bytes": MAX_FILE_BYTES,
                "evaluation_available": (ws.evals_root / "cases").exists(),
            })
        if parts == ["validate"] and method == "POST":
            body = self._body()
            v = ws.validate_inputs(_files(body))
            return self._json(200, {"ok": v.ok, "report": v.report, "summary": ws.input_summary(v.data)})
        if parts == ["sessions"] and method == "POST":
            body = self._body()
            actor = str(body.get("actor") or "").strip()
            if not actor:
                raise WorkbenchError("reviewer name is required")
            with self.server.lock:
                if body.get("example"):
                    meta = ws.create_session_from_example(str(body["example"]), actor=actor,
                                                          include_outcomes=bool(body.get("include_outcomes", True)))
                else:
                    meta = ws.create_session(_files(body), source="upload", actor=actor)
            return self._json(201, meta)
        if len(parts) >= 2 and parts[0] == "sessions":
            sid = parts[1]
            if len(parts) == 2 and method == "GET":
                return self._json(200, ws.session(sid))
            if len(parts) == 2 and method == "DELETE":
                body = self._body()
                with self.server.lock:
                    ws.delete_session(sid, actor=_actor(body), reason=str(body.get("reason") or "deleted by reviewer")[:200])
                return self._json(200, {"deleted": sid})
            if parts[2:] == ["runs"] and method == "POST":
                body = self._body()
                with self.server.lock:
                    run = ws.run(sid, str(body.get("knowledge") or "env:production"), actor=_actor(body))
                return self._json(201, run)
            if len(parts) >= 4 and parts[2] == "runs":
                rid = parts[3]
                rest = parts[4:]
                if not rest and method == "GET":
                    return self._json(200, ws.load_run(sid, rid))
                if rest == ["verify"] and method == "POST":
                    return self._json(200, ws.verify_run(sid, rid, actor=_actor(self._body())))
                if rest == ["finding-decisions"] and method == "POST":
                    b = self._body()
                    with self.server.lock:
                        entry = ws.record_finding_decision(sid, rid, str(b.get("finding_id")), str(b.get("disposition")),
                                                           b.get("rationale"), b.get("actor"))
                    return self._json(201, entry)
                if rest == ["candidate-decisions"] and method == "POST":
                    b = self._body()
                    with self.server.lock:
                        entry = ws.record_candidate_decision(sid, rid, str(b.get("candidate_id")), str(b.get("disposition")),
                                                             b.get("rationale"), b.get("actor"), b.get("review_minutes"))
                    return self._json(201, entry)
                if len(rest) == 2 and rest[0] == "export" and method == "GET":
                    data, ctype, filename = ws.export(sid, rid, rest[1], actor="workbench")
                    safe = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
                    self._headers(200, ctype, len(data), {"Content-Disposition": f'attachment; filename="{safe}"'})
                    return self.wfile.write(data)
        if parts == ["evaluate"] and method == "POST":
            b = self._body()
            return self._json(200, ws.evaluate(str(b.get("knowledge") or "pack")))
        if parts == ["compare"] and method == "POST":
            b = self._body()
            return self._json(200, ws.compare(str(b.get("baseline") or "env:production"), str(b.get("candidate") or "pack")))
        raise WorkbenchError("not found", status=404)


def _files(body: dict[str, Any]) -> dict[str, str]:
    files = body.get("files")
    if not isinstance(files, dict):
        raise WorkbenchError("'files' must map input kinds to file contents")
    return {str(k): v for k, v in files.items() if v not in (None, "")}


def _actor(body: dict[str, Any]) -> str:
    actor = str(body.get("actor") or "").strip()
    if not actor:
        raise WorkbenchError("reviewer name is required")
    return actor[:200]


def make_server(workspace: Workspace, host: str = "127.0.0.1", port: int = 8765, *,
                allow_remote: bool = False, token: str | None = None, quiet: bool = False) -> WorkbenchServer:
    if not is_loopback(host) and not allow_remote:
        raise WorkbenchError(f"refusing to bind to non-loopback address {host!r}; candidate evidence must not be "
                             "exposed to the network (pass --allow-remote only behind your own access controls)")
    return WorkbenchServer((host, port), workspace, token=token, quiet=quiet)


__all__ = ["make_server", "WorkbenchServer", "EXPORTS"]
