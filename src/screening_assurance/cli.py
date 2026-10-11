"""Command-line interface: `sa` / `screening-assurance`.

    sa workbench                           open the local Candidate Rediscovery Workbench (recruiter UI)
    sa diagnose <requisition-dir>          run the diagnostic loop and write the assurance report
    sa discover <requisition-dir>          candidate rediscovery over applicants and an authorized pool
    sa portfolio <dir>                     portfolio overview across requisitions
    sa eval                                regression-test the knowledge pack against labeled cases
    sa eval-compare --baseline A --candidate B   before/after comparison when knowledge changes
    sa knowledge validate|diff|status|release|promote|rollback|propose|proposals
    sa propose-from-decisions <requisition-dir>  turn reviewer suggestions into knowledge proposals
    sa schema <name>                       print a data contract (JSON Schema)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from . import __version__
from .contracts import ContractError, _schema, load
from .engine import diagnose, load_bundle
from .evals import compare_suites, render_compare_markdown, render_suite_markdown, run_suite
from .knowledge import KnowledgeRegistry, diff_packs, load_pack, validate_pack
from .knowledge.diff import format_diff
from .report import build_portfolio, render_changes, render_html, render_markdown, render_portfolio_markdown


def _registry(args: argparse.Namespace) -> KnowledgeRegistry:
    return KnowledgeRegistry(args.knowledge_root or os.environ.get("SA_KNOWLEDGE_ROOT", "knowledge"))


def _pack(args: argparse.Namespace, spec: str | None = None):
    return _registry(args).load(spec if spec is not None else getattr(args, "knowledge", None))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _print(msg: str = "") -> None:
    print(msg)


# ------------------------------------------------------------------ diagnose
def cmd_diagnose(args: argparse.Namespace) -> int:
    pack = _pack(args)
    bundle = load_bundle(args.requisition, policy=args.policy)
    result = diagnose(bundle, pack, run_at=args.run_at).as_dict()
    out = Path(args.out) / result["requisition"]["id"]
    formats = set(args.format.split(","))
    if "json" in formats:
        _write(out / "findings.json", json.dumps(result, indent=2, default=str) + "\n")
    if "md" in formats:
        _write(out / "report.md", render_markdown(result))
    if "html" in formats:
        _write(out / "report.html", render_html(result))
    changes = render_changes(result, include_pending=args.include_pending)
    _write(out / "changes.yaml", yaml.safe_dump(changes, sort_keys=False))
    s = result["summary"]
    _print(f"{result['requisition']['id']} {result['requisition']['title']}  [knowledge {result['knowledge']['fingerprint']}]")
    _print(f"  Level 1 inconsistencies: {s['by_level']['level_1']}   Level 2 risks/opportunities: {s['by_level']['level_2']}   "
           f"Level 3 measured: {s['by_level']['level_3']}")
    _print(f"  Candidates surfaced for review: {s['candidates_surfaced']} of {s['candidates_assessed']}   "
           f"Pending decisions: {s['pending_decisions']}   Accepted changes: {len(changes['changes']) if not args.include_pending else '-'}")
    _print(f"  Wrote {out}/")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    from .engine import discover
    from .report.discovery import render_discovery_markdown
    pack = _pack(args)
    bundle = load_bundle(args.requisition, policy=args.policy)
    if args.pool:
        bundle.pool = load("candidate_pool", args.pool)
    diag = diagnose(bundle, pack, run_at=args.run_at)
    res = discover(bundle, pack, diag, as_of=args.as_of).as_dict()
    out = Path(args.out) / res["requisition_id"]
    _write(out / "discovery.json", json.dumps(res, indent=2, default=str) + "\n")
    _write(out / "discovery.md", render_discovery_markdown(res).lstrip() + "\n")
    c = res["counts"]
    _print(f"{res['requisition_id']} [knowledge {res['knowledge']}] as of {res['as_of']}")
    _print("  " + "   ".join(f"{k.replace('_', ' ')}: {v}" for k, v in c.items()))
    _print(f"  Wrote {out}/discovery.md")
    return 0


def cmd_workbench(args: argparse.Namespace) -> int:
    import webbrowser
    from .workbench.server import make_server
    from .workbench.workspace import Workspace
    ws = Workspace(args.workspace, knowledge_root=args.knowledge_root or os.environ.get("SA_KNOWLEDGE_ROOT", "knowledge"),
                   examples_root=args.examples, evals_root=args.evals)
    purged = ws.purge_expired()
    if purged:
        _print(f"Retention: removed candidate data from {len(purged)} expired session(s).")
    srv = make_server(ws, args.host, args.port, allow_remote=args.allow_remote)
    _print(f"Candidate Rediscovery Workbench running at {srv.url}")
    _print(f"Workspace: {Path(args.workspace).resolve()}  (candidate data stays on this computer)")
    _print("Press Ctrl+C to stop.")
    if not args.no_browser:
        webbrowser.open(srv.url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        _print("\nStopped.")
    finally:
        srv.server_close()
    return 0


def _requisition_dirs(root: Path) -> list[Path]:
    return sorted(p.parent for p in root.rglob("requisition.yaml"))


def cmd_portfolio(args: argparse.Namespace) -> int:
    pack = _pack(args)
    results = []
    for d in _requisition_dirs(Path(args.root)):
        results.append(diagnose(load_bundle(d), pack, run_at=args.run_at).as_dict())
    p = build_portfolio(results)
    md = render_portfolio_markdown(p)
    if args.out:
        _write(Path(args.out) / "portfolio.md", md)
        _write(Path(args.out) / "portfolio.json", json.dumps(p, indent=2) + "\n")
        _print(f"Wrote {args.out}/portfolio.md")
    else:
        _print(md)
    return 0


# ------------------------------------------------------------------ eval
def cmd_eval(args: argparse.Namespace) -> int:
    pack = _pack(args)
    th = yaml.safe_load(Path(args.thresholds).read_text()) if args.thresholds else None
    suite = run_suite(args.cases, pack, th)
    md = render_suite_markdown(suite)
    if args.out:
        _write(Path(args.out), md)
        _write(Path(args.out).with_suffix(".json"), json.dumps(suite, indent=2, default=str) + "\n")
    if args.json:
        _print(json.dumps({k: suite[k] for k in ("knowledge", "metrics", "passed", "failures")}, indent=2))
    else:
        _print(md if not args.out else f"Eval {'PASS' if suite['passed'] else 'FAIL'} — wrote {args.out}")
    return 0 if suite["passed"] else 1


def cmd_eval_compare(args: argparse.Namespace) -> int:
    th = yaml.safe_load(Path(args.thresholds).read_text()) if args.thresholds else None
    base = run_suite(args.cases, _pack(args, args.baseline), th)
    cand = run_suite(args.cases, _pack(args, args.candidate), th)
    cmp = compare_suites(base, cand)
    kdiff = diff_packs(_pack(args, args.baseline), _pack(args, args.candidate))
    md = render_compare_markdown(cmp) + "\n## Knowledge records changed\n\n```\n" + format_diff(kdiff) + "\n```\n"
    if args.out:
        _write(Path(args.out), md)
        _print(f"Regression gate {'PASS' if cmp['passed'] else 'FAIL'} — wrote {args.out}")
    else:
        _print(md)
    return 0 if cmp["passed"] else 1


# ------------------------------------------------------------------ knowledge
def cmd_k_validate(args: argparse.Namespace) -> int:
    path = _registry(args).resolve(args.knowledge)
    rep = validate_pack(path)
    if args.json:
        _print(json.dumps(rep.as_dict(), indent=2))
    else:
        _print(f"{'OK' if rep.ok else 'INVALID'}  {path}  version {rep.version}  {rep.counts}")
        for e in rep.errors:
            _print(f"  error: {e}")
        for w in rep.warnings:
            _print(f"  warning: {w}")
    return 0 if rep.ok else 1


def cmd_k_diff(args: argparse.Namespace) -> int:
    d = diff_packs(_pack(args, args.old), _pack(args, args.new))
    _print(json.dumps(d, indent=2) if args.json else format_diff(d))
    return 0


def cmd_k_status(args: argparse.Namespace) -> int:
    reg = _registry(args)
    pack = load_pack(reg.pack_dir)
    dep = reg.deployments()
    _print(f"Working pack: {pack.fingerprint} (status: {pack.manifest['status']})")
    _print(f"Releases: {', '.join(reg.releases()) or '—'}")
    for env, v in dep["environments"].items():
        _print(f"  {env}: {v}")
    if dep["history"]:
        _print("History:")
        for h in dep["history"][-10:]:
            _print(f"  {h['at']}  {h['action']:8} {h['environment']:11} {h.get('previous') or '—'} -> {h['version']}  by {h['by']}: {h['reason']}")
    props = [p for p in reg.proposals() if p["status"] == "open"]
    _print(f"Open proposals: {len(props)}")
    return 0


def _gate(args: argparse.Namespace, spec: str) -> dict[str, Any] | None:
    if args.skip_eval:
        return {"passed": None, "skipped": True}
    suite = run_suite(args.cases, _pack(args, spec))
    if not suite["passed"]:
        _print("Evaluation failed; refusing to continue:")
        for f in suite["failures"]:
            _print(f"  - {f}")
        return None
    return {"passed": True, "metrics": suite["metrics"], "knowledge": suite["knowledge"]}


def cmd_k_release(args: argparse.Namespace) -> int:
    reg = _registry(args)
    summary = _gate(args, "pack")
    if summary is None:
        return 1
    dest = reg.release(args.by, summary)
    _print(f"Released {dest.name} -> {dest}")
    return 0


def cmd_k_promote(args: argparse.Namespace) -> int:
    reg = _registry(args)
    summary = _gate(args, f"release:{args.version}")
    if summary is None:
        return 1
    reg.promote(args.version, args.env, args.by, args.reason, summary)
    _print(f"Promoted {args.version} to {args.env}")
    return 0


def cmd_k_rollback(args: argparse.Namespace) -> int:
    v = _registry(args).rollback(args.env, args.by, args.reason)
    _print(f"Rolled {args.env} back to {v}")
    return 0


def cmd_k_propose(args: argparse.Namespace) -> int:
    prop = {
        "submitted_by": args.by, "document": args.document, "change": args.change, "rationale": args.rationale,
    }
    if args.target:
        prop["target_record"] = args.target
    ctx = {k: v for k, v in (("requisition_id", args.requisition), ("finding_id", args.finding), ("job_family", args.job_family)) if v}
    if ctx:
        prop["context"] = ctx
    path = _registry(args).propose(prop)
    _print(f"Proposal recorded at {path}. It will not affect diagnostics until an administrator approves a knowledge revision.")
    return 0


def cmd_k_proposals(args: argparse.Namespace) -> int:
    for p in _registry(args).proposals():
        _print(f"{p['id']} [{p['status']}] {p['document']}{' / ' + p['target_record'] if p.get('target_record') else ''} — {p['change']} (by {p['submitted_by']})")
    return 0


def cmd_propose_from_decisions(args: argparse.Namespace) -> int:
    bundle = load_bundle(args.requisition)
    if not bundle.decisions:
        _print("No decisions.yaml found.")
        return 1
    result = diagnose(bundle, _pack(args)).as_dict()
    by_id = {f["id"]: f for f in result["findings"]}
    reg = _registry(args)
    n = 0
    for d in bundle.decisions["decisions"]:
        if not d.get("propose_knowledge_update"):
            continue
        f = by_id.get(d["finding_id"])
        if not f:
            continue
        doc = "equivalencies" if any(r.startswith("eq.") for r in f["knowledge_refs"]) else "synonyms"
        prop = {
            "submitted_by": d["decided_by"], "document": doc,
            "change": f"Reviewer {d['disposition']} finding '{f['title']}'",
            "rationale": d["rationale"],
            "context": {"requisition_id": result["requisition"]["id"], "finding_id": f["id"],
                        "job_family": result["requisition"]["job_family"]},
        }
        if f["knowledge_refs"]:
            prop["target_record"] = f["knowledge_refs"][0]
        reg.propose(prop)
        n += 1
    _print(f"Created {n} knowledge proposal(s). Proposals never change production knowledge without administrator review.")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    _print(json.dumps(_schema(args.name), indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    load(args.contract, args.path)
    _print(f"OK  {args.path} satisfies the '{args.contract}' contract")
    return 0


# ------------------------------------------------------------------ parser
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sa", description="Screening Assurance — screening-quality layer for existing ATS platforms.")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--knowledge-root", help="knowledge root directory (default: ./knowledge or $SA_KNOWLEDGE_ROOT)")
    sub = p.add_subparsers(dest="cmd", required=True)
    kspec = "knowledge to use: 'pack' (working copy, default), 'release:<ver>', 'env:<name>', or a path"

    d = sub.add_parser("diagnose", help="run diagnostics for one requisition directory")
    d.add_argument("requisition")
    d.add_argument("--knowledge", default=None, help=kspec)
    d.add_argument("--policy", help="employer policy file (default: nearest policy.yaml)")
    d.add_argument("--out", default="out")
    d.add_argument("--format", default="md,html,json")
    d.add_argument("--run-at", help="fixed timestamp for reproducible output")
    d.add_argument("--include-pending", action="store_true", help="include pending findings in changes.yaml")
    d.set_defaults(func=cmd_diagnose)

    wb = sub.add_parser("workbench", help="open the local recruiter workbench in your browser")
    wb.add_argument("--host", default="127.0.0.1", help="bind address (loopback only unless --allow-remote)")
    wb.add_argument("--port", type=int, default=8765)
    wb.add_argument("--workspace", default="workspace", help="local working area for sessions and runs")
    wb.add_argument("--examples", default="examples")
    wb.add_argument("--evals", default="evals")
    wb.add_argument("--no-browser", action="store_true")
    wb.add_argument("--allow-remote", action="store_true", help=argparse.SUPPRESS)
    wb.set_defaults(func=cmd_workbench)

    ds = sub.add_parser("discover", help="candidate rediscovery for one requisition directory")
    ds.add_argument("requisition")
    ds.add_argument("--knowledge", default=None, help=kspec)
    ds.add_argument("--policy")
    ds.add_argument("--pool", help="candidate pool file (default: candidate-pool.yaml in the requisition directory)")
    ds.add_argument("--as-of", help="assessment date for evidence freshness (default: pool export date)")
    ds.add_argument("--run-at")
    ds.add_argument("--out", default="out")
    ds.set_defaults(func=cmd_discover)

    pf = sub.add_parser("portfolio", help="portfolio overview across all requisitions under a directory")
    pf.add_argument("root")
    pf.add_argument("--knowledge", default=None, help=kspec)
    pf.add_argument("--out")
    pf.add_argument("--run-at")
    pf.set_defaults(func=cmd_portfolio)

    e = sub.add_parser("eval", help="run the evaluation suite")
    e.add_argument("--knowledge", default=None, help=kspec)
    e.add_argument("--cases", default="evals/cases")
    e.add_argument("--thresholds", default="evals/thresholds.yaml" if Path("evals/thresholds.yaml").exists() else None)
    e.add_argument("--out")
    e.add_argument("--json", action="store_true")
    e.set_defaults(func=cmd_eval)

    ec = sub.add_parser("eval-compare", help="compare two knowledge versions on the evaluation suite")
    ec.add_argument("--baseline", required=True, help=kspec)
    ec.add_argument("--candidate", default="pack", help=kspec)
    ec.add_argument("--cases", default="evals/cases")
    ec.add_argument("--thresholds", default="evals/thresholds.yaml" if Path("evals/thresholds.yaml").exists() else None)
    ec.add_argument("--out")
    ec.set_defaults(func=cmd_eval_compare)

    k = sub.add_parser("knowledge", help="manage versioned knowledge")
    ks = k.add_subparsers(dest="kcmd", required=True)
    kv = ks.add_parser("validate"); kv.add_argument("--knowledge", default=None, help=kspec); kv.add_argument("--json", action="store_true"); kv.set_defaults(func=cmd_k_validate)
    kd = ks.add_parser("diff"); kd.add_argument("old"); kd.add_argument("new"); kd.add_argument("--json", action="store_true"); kd.set_defaults(func=cmd_k_diff)
    kst = ks.add_parser("status"); kst.set_defaults(func=cmd_k_status)
    kr = ks.add_parser("release", help="snapshot the approved working pack as an immutable release")
    kr.add_argument("--by", required=True); kr.add_argument("--cases", default="evals/cases"); kr.add_argument("--skip-eval", action="store_true"); kr.set_defaults(func=cmd_k_release)
    kp = ks.add_parser("promote", help="promote a release to an environment (runs the eval gate)")
    kp.add_argument("version"); kp.add_argument("--env", required=True); kp.add_argument("--by", required=True); kp.add_argument("--reason", required=True)
    kp.add_argument("--cases", default="evals/cases"); kp.add_argument("--skip-eval", action="store_true"); kp.set_defaults(func=cmd_k_promote)
    kb = ks.add_parser("rollback"); kb.add_argument("--env", required=True); kb.add_argument("--by", required=True); kb.add_argument("--reason", required=True); kb.set_defaults(func=cmd_k_rollback)
    kpr = ks.add_parser("propose", help="submit a knowledge correction (does not change production knowledge)")
    kpr.add_argument("--by", required=True); kpr.add_argument("--document", required=True, choices=["synonyms", "equivalencies", "skills"])
    kpr.add_argument("--change", required=True); kpr.add_argument("--rationale", required=True); kpr.add_argument("--target")
    kpr.add_argument("--requisition"); kpr.add_argument("--finding"); kpr.add_argument("--job-family"); kpr.set_defaults(func=cmd_k_propose)
    kl = ks.add_parser("proposals"); kl.set_defaults(func=cmd_k_proposals)

    pd = sub.add_parser("propose-from-decisions", help="create knowledge proposals from reviewer decisions")
    pd.add_argument("requisition"); pd.add_argument("--knowledge", default=None, help=kspec); pd.set_defaults(func=cmd_propose_from_decisions)

    sc = sub.add_parser("schema", help="print a data contract")
    sc.add_argument("name", choices=["synonyms", "skills", "equivalencies", "manifest", "policy", "requisition",
                                     "candidates", "candidate_pool", "decisions", "review_decisions", "outcomes",
                                     "eval_case", "discovery_case", "proposal", "common"])
    sc.set_defaults(func=cmd_schema)

    ch = sub.add_parser("check", help="validate a file against a data contract")
    ch.add_argument("contract", choices=["policy", "requisition", "candidates", "candidate_pool", "decisions",
                                         "review_decisions", "outcomes", "eval_case", "discovery_case", "proposal"])
    ch.add_argument("path"); ch.set_defaults(func=cmd_check)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:  # WorkbenchError and similar user-facing errors
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
