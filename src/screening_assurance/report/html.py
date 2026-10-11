"""Self-contained HTML requisition assurance report with a decision-capture workflow.

Reviewers accept / reject / defer each finding with a rationale, then export a
decisions.yaml that is fed back into the next run. The page never changes ATS
configuration and works offline (no external assets).
"""

from __future__ import annotations

import json
from html import escape
from typing import Any

import yaml

from .common import (
    CATEGORY_TITLE,
    CLASSIFICATION_LABEL,
    DISPOSITIONS,
    STATUS_LABEL,
    candidate_review_answers,
)

CSS = """
:root{--bg:#f7f6f3;--surface:#ffffff;--ink:#1d1d1b;--muted:#5f5e5a;--line:#e3e1db;--accent:#1f5f8b;
--l1:#9a3412;--l1bg:#fdf0e8;--l2:#7c5e10;--l2bg:#fbf5e3;--l3:#1e6b3a;--l3bg:#e9f5ee;--ok:#1e6b3a;--warn:#9a3412;
--chip:#efede7;--code:#f1efe9}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151514;--surface:#1e1e1c;--ink:#ecebe6;--muted:#a3a19a;
--line:#34332f;--accent:#7cb4dd;--l1:#f0a27a;--l1bg:#3a2419;--l2:#e2c473;--l2bg:#352d17;--l3:#8fd1a6;--l3bg:#1b3125;
--ok:#8fd1a6;--warn:#f0a27a;--chip:#2a2926;--code:#262522}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
header.top{background:var(--surface);border-bottom:1px solid var(--line);padding:28px 16px 20px}
.wrap{max-width:1060px;margin:0 auto;padding:0 16px}
h1{font-size:26px;line-height:1.25;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:19px;margin:40px 0 12px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:0 0 6px;line-height:1.35}
.meta{color:var(--muted);font-size:13px}
.meta code{font-size:12px}
code{background:var(--code);padding:1px 5px;border-radius:4px;font:12.5px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}
.note{border-left:3px solid var(--accent);padding:8px 12px;background:var(--surface);color:var(--muted);font-size:13.5px;margin:16px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0 6px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.stat b{display:block;font-size:24px;line-height:1.1}
.stat span{color:var(--muted);font-size:12.5px}
nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 0}
nav.toc a{font-size:12.5px;color:var(--accent);text-decoration:none;background:var(--chip);padding:3px 9px;border-radius:999px}
.tbl{width:100%;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--surface);border:1px solid var(--line);border-radius:8px}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--line)}
th{font-weight:600;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.03em}
tr:last-child td{border-bottom:0}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.card .head{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
.badge{font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap}
.b1{color:var(--l1);background:var(--l1bg)}.b2{color:var(--l2);background:var(--l2bg)}.b3{color:var(--l3);background:var(--l3bg)}
.chip{font-size:11.5px;color:var(--muted);background:var(--chip);padding:2px 8px;border-radius:999px}
.kv{display:grid;grid-template-columns:150px 1fr;gap:4px 14px;font-size:14px;margin:10px 0}
.kv dt{color:var(--muted)}.kv dd{margin:0}
ul{margin:4px 0 8px;padding-left:20px}
li{margin:2px 0}
.ev{font-size:13.5px}
.ev .src{color:var(--muted);font:12px ui-monospace,SFMono-Regular,Menlo,monospace}
details{margin-top:8px}
summary{cursor:pointer;color:var(--accent);font-size:13.5px}
.decision{margin-top:12px;padding-top:12px;border-top:1px dashed var(--line);display:grid;grid-template-columns:220px 1fr;gap:8px;align-items:start}
.decision select,.decision textarea,.who input{font:inherit;font-size:13.5px;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:6px 8px;width:100%}
.decision textarea{min-height:38px;resize:vertical}
.decided{font-size:13.5px;color:var(--ok)}
.st-evidenced,.st-alternative_path{color:var(--ok)}.st-not_evidenced,.st-protected_missing,.st-insufficient{color:var(--warn)}
.st-pending_clarification{color:var(--muted)}
.bar{position:sticky;bottom:0;background:var(--surface);border-top:1px solid var(--line);padding:10px 0;margin-top:40px}
.bar .wrap{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.who{display:flex;gap:8px;align-items:center;flex:1;min-width:240px}
.who input{max-width:280px}
button{font:inherit;font-size:14px;border:0;border-radius:8px;padding:8px 14px;background:var(--accent);color:#fff;cursor:pointer}
button.ghost{background:var(--chip);color:var(--ink)}
#count{color:var(--muted);font-size:13px}
pre{background:var(--code);padding:10px;border-radius:8px;overflow:auto;font-size:12.5px}
@media (max-width:640px){.bar{position:static}.kv{grid-template-columns:1fr}.decision{grid-template-columns:1fr}h1{font-size:22px}}
"""

JS = """
const KEY='sa-decisions-'+document.body.dataset.req;
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function save(s){try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
const state=load();
function refresh(){let n=0;document.querySelectorAll('[data-fid]').forEach(el=>{if(el.querySelector('select').value)n++});
document.getElementById('count').textContent=n+' decision'+(n==1?'':'s')+' recorded in this browser';}
document.querySelectorAll('[data-fid]').forEach(el=>{const id=el.dataset.fid,sel=el.querySelector('select'),ta=el.querySelector('textarea');
 if(state[id]){sel.value=state[id].d||'';ta.value=state[id].r||''}
 const upd=()=>{state[id]={d:sel.value,r:ta.value};save(state);refresh()};sel.onchange=upd;ta.oninput=upd;});
const who=document.getElementById('who');try{who.value=localStorage.getItem('sa-who')||''}catch(e){}
who.oninput=()=>{try{localStorage.setItem('sa-who',who.value)}catch(e){}};
function q(s){return JSON.stringify(s)}
function build(){const by=who.value.trim()||'reviewer@example.com';const now=new Date().toISOString().slice(0,19)+'Z';
 let y='requisition_id: '+q(document.body.dataset.req)+'\\ndecisions:\\n';let n=0,missing=[];
 document.querySelectorAll('[data-fid]').forEach(el=>{const d=el.querySelector('select').value,r=el.querySelector('textarea').value.trim();
  if(!d)return; if(!r){missing.push(el.dataset.fid);return}
  n++;y+='  - finding_id: '+q(el.dataset.fid)+'\\n    disposition: '+d+'\\n    rationale: '+q(r)+'\\n    decided_by: '+q(by)+'\\n    decided_at: '+q(now)+'\\n';});
 if(!n)y+='  []\\n';return {y,missing};}
document.getElementById('export').onclick=()=>{const {y,missing}=build();
 if(missing.length&&!confirm('A rationale is required. '+missing.length+' decision(s) without rationale will be left out. Continue?'))return;
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([y],{type:'text/yaml'}));a.download='decisions.yaml';a.click();};
document.getElementById('show').onclick=()=>{const p=document.getElementById('preview');p.hidden=!p.hidden;p.textContent=build().y;};
refresh();
"""


def e(s: Any) -> str:
    return escape("" if s is None else str(s))


def _badge(level: int) -> str:
    label = {1: "Level 1 · Demonstrable inconsistency", 2: "Level 2 · Missed-talent risk", 3: "Level 3 · Measured impact"}[level]
    return f'<span class="badge b{level}">{label}</span>'


def _decision_controls(f: dict[str, Any]) -> str:
    d = f["disposition"]
    if d.get("status") == "not_required":
        return '<p class="meta">Measured outcome — no decision required.</p>'
    recorded = ""
    if d.get("status", "pending") != "pending":
        recorded = (f'<div class="decided">Recorded decision: <b>{e(d["status"])}</b> by {e(d.get("decided_by"))} '
                    f'({e(d.get("decided_at"))}) — {e(d.get("rationale"))}</div>')
    opts = '<option value="">— decision —</option>' + "".join(
        f'<option value="{v}">{e(label)}</option>' for v, label in DISPOSITIONS)
    return (f'{recorded}<div class="decision" data-fid="{e(f["id"])}"><select aria-label="Decision">{opts}</select>'
            f'<textarea placeholder="Rationale (required)" aria-label="Rationale"></textarea></div>')


def _evidence_list(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    lis = "".join(f'<li class="ev"><span class="src">{e(i.get("source"))}</span><br>{e(i.get("text"))}</li>' for i in items)
    return f"<ul>{lis}</ul>"


def _finding_card(result: dict[str, Any], f: dict[str, Any]) -> str:
    parts = [f'<article class="card" id="{e(f["id"])}"><div class="head">{_badge(f["evidence_level"])}'
             f'<span class="chip">{e(CATEGORY_TITLE[f["category"]])}</span><span class="chip">confidence: {e(f["confidence"])}</span>'
             f'<span class="chip"><code>{e(f["id"])}</code></span></div><h3>{e(f["title"])}</h3><p>{e(f["observation"])}</p>']
    if f["category"] == "candidate_review_opportunity":
        parts.append(_candidate_view(result, f))
    else:
        parts.append(_evidence_list(f["evidence"]))
        if f["category"] != "measured_impact" and (f.get("affected_candidates") or f.get("unlocked_candidates")):
            parts.append(
                f'<p><b>Consequence in the supplied sample:</b> {len(f["affected_candidates"])} candidate(s) pass this rule under this '
                f'correction alone{(" (" + e(", ".join(f["affected_candidates"])) + ")") if f["affected_candidates"] else ""}; '
                f'{len(f["unlocked_candidates"])} candidate-review opportunit{"y depends" if len(f["unlocked_candidates"]) == 1 else "ies depend"} on it'
                f'{(" (" + e(", ".join(f["unlocked_candidates"])) + ")") if f["unlocked_candidates"] else ""}.</p>')
        parts.append(f'<dl class="kv"><dt>Proposed action</dt><dd>{e(f["proposed_action"])}</dd>'
                     f'<dt>Expected benefit</dt><dd>{e(f["expected_benefit"])}</dd>'
                     f'<dt>Trade-off</dt><dd>{e(f["tradeoffs"])}</dd></dl>')
        if f.get("proposed_change"):
            parts.append(f'<details><summary>Suggested configuration change (simulation only)</summary><pre>{e(yaml.safe_dump(f["proposed_change"], sort_keys=False))}</pre></details>')
        if f["limitations"]:
            parts.append("<details><summary>Limitations</summary><ul>" + "".join(f"<li>{e(l)}</li>" for l in f["limitations"]) + "</ul></details>")
    refs = ", ".join(f"{r['kind']}:{r['id']}" for r in f["source_refs"])
    parts.append(f'<p class="meta">Sources: {e(refs)} · knowledge <code>{e(f["knowledge_version"])}</code>'
                 + (f' · records: {e(", ".join(f["knowledge_refs"]))}' if f["knowledge_refs"] else "") + "</p>")
    parts.append(_decision_controls(f))
    parts.append("</article>")
    return "".join(parts)


def _candidate_view(result: dict[str, Any], f: dict[str, Any]) -> str:
    a = candidate_review_answers(result, f)
    rows = []
    for r in a["requirements"]:
        ev = "".join(f'<div class="ev"><span class="src">{e(x["source"].split("/")[-1])}</span> {e(x["text"])}</div>' for x in r["evidence"][:2]) or "—"
        months = f' · {r["months"]} mo' if r["months"] is not None else ""
        rows.append(f'<tr><td><b>{e(r["id"])}</b><br><span class="meta">{e(r["stated_as"])}</span></td><td>{e(r["text"])}</td>'
                    f'<td class="st-{e(r["status"])}">{e(STATUS_LABEL[r["status"]])}{e(months)}<br><span class="meta">{e(", ".join(r["paths"]))}</span></td>'
                    f'<td>{ev}</td></tr>')
    html = ['<p><b>What requirement might this person satisfy, and what evidence supports it?</b></p>',
            '<div class="tbl"><table><thead><tr><th>Req</th><th>Requirement</th><th>Status · path</th><th>Evidence</th></tr></thead><tbody>',
            "".join(rows), "</tbody></table></div>",
            "<p><b>Excluded by:</b> " + e("; ".join(f"{o['rule_id']} — {o['reason']}" for o in a["excluded_by"])) + "</p>"]
    if a["differs"]:
        html.append("<p><b>How their experience differs from the conventional path</b></p><ul>" + "".join(f"<li>{e(x)}</li>" for x in a["differs"]) + "</ul>")
    html.append("<p><b>What remains unproven</b></p><ul>" + "".join(f"<li>{e(x)}</li>" for x in a["unproven"]) + "</ul>")
    html.append("<p><b>What to verify next</b></p><ul>" + "".join(f"<li>{e(x)}</li>" for x in a["verify"]) + "</ul>")
    if f.get("related_findings"):
        html.append('<p class="meta">Surfaced because of: ' + ", ".join(f'<a href="#{e(x)}">{e(x)}</a>' for x in f["related_findings"]) + "</p>")
    return "".join(html)


def _measurement_html(result: dict[str, Any]) -> str:
    m = result.get("measurement")
    if not m:
        return '<p class="meta">No outcome data supplied yet. Add <code>outcomes.yaml</code> with a documented baseline after corrections are implemented.</p>'
    me = m["measured"]
    rows = "".join(f"<tr><td>{e(k.replace('_', ' '))}</td><td>{e(v if v is not None else '—')}</td></tr>" for k, v in me.items())
    html = [f'<p>Comparison method: <b>{e(m["comparison_method"])}</b></p><h3>Measured</h3><div class="tbl"><table><tbody>{rows}</tbody></table></div>']
    if m.get("baseline"):
        b, a, d = m["baseline"], m.get("after_change") or {}, m.get("deltas") or {}
        trs = "".join(
            f"<tr><td>{e(k.replace('_', ' '))}</td><td>{e(b.get(k, '—'))}</td><td>{e(a.get(k, '—'))}</td><td>{e(d.get(k, '—'))}</td></tr>"
            for k in ("applicants", "recruiter_reviewed", "qualified_candidates", "recruiter_hours", "qualified_yield",
                      "recruiter_hours_per_qualified", "days_to_qualified_shortlist"))
        html.append(f'<h3 style="margin-top:16px">Baseline vs. after change</h3><div class="tbl"><table><thead><tr><th>Metric</th><th>Baseline</th><th>After</th><th>Δ</th></tr></thead><tbody>{trs}</tbody></table></div>')
    if m.get("estimated"):
        est = m["estimated"]
        items = "".join(f"<li>{e(k.replace('_', ' '))}: {e(v)}</li>" for k, v in est.items() if k not in ("label", "assumptions"))
        html.append(f'<h3 style="margin-top:16px">{e(est["label"])}</h3><ul>{items}</ul><p class="meta">Assumptions: {e(est["assumptions"])}</p>')
    if m.get("attribution"):
        trs = "".join(f'<tr><td><a href="#{e(a["finding_id"])}">{e(a["finding_id"])}</a><br>{e(a["title"])}</td><td>{a["reviewed"]}</td>'
                      f'<td>{a["meets_requirements"]}</td><td>{a["review_minutes"]:g}</td></tr>' for a in m["attribution"])
        html.append('<h3 style="margin-top:16px">Attribution</h3><div class="tbl"><table><thead><tr><th>Correction</th><th>Reviewed</th>'
                    f'<th>Met requirements</th><th>Minutes</th></tr></thead><tbody>{trs}</tbody></table></div>')
    html.append(f'<p class="meta">{e(m["attribution_note"])}</p>')
    return "".join(html)


def render_html(result: dict[str, Any], discovery: dict[str, Any] | None = None,
                review_decisions: dict[str, Any] | None = None) -> str:
    from .discovery import render_discovery_html
    discovery_html = render_discovery_html(discovery, review_decisions) if discovery else ""
    req = result["requisition"]
    s = result["summary"]
    lv = s["by_level"]
    F = result["findings"]

    def section(cats: tuple[str, ...]) -> str:
        items = [f for f in F if f["category"] in cats]
        return "".join(_finding_card(result, f) for f in items) or '<p class="meta">None found.</p>'

    req_rows = "".join(
        f'<tr><td><b>{e(r["id"])}</b></td><td>{e(r["text"])}</td><td>{e(r["stated_as"])}</td>'
        f'<td>{e(CLASSIFICATION_LABEL[r["proposed_classification"]])}{" 🔒" if r["protected"] else ""}</td><td class="meta">{e(r["classification_basis"])}</td></tr>'
        for r in result["requirements"])
    rule_rows = "".join(
        f'<tr><td><b>{e(r["id"])}</b></td><td>{e(r["text"])}<br><span class="meta">{e(r["type"])} · {e(r["action"])}</span></td>'
        f'<td>{e(r["linked_requirement"] or "— none")}</td><td>{e(r["status"].replace("_", " "))}</td>'
        f'<td>{"".join(f"<a href=#{e(x)}>{e(x[-8:])}</a> " for x in r["finding_ids"]) or "—"}</td></tr>'
        for r in result["rules"])
    not_surfaced = "".join(
        f'<tr><td><b>{e(c["candidate_id"])}</b></td><td>{e(c["ats_status"])}</td><td>{e(", ".join(c["excluded_by"]) or "—")}</td><td>{e(c["reason"])}</td></tr>'
        for c in result["candidates"] if not c["surfaced"])
    suppressed = "".join(f'<li>{e(x["kind"])} <code>{e(x["id"])}</code>: {e(x["reason"])}</li>' for x in result["suppressed"])
    decided = [f for f in F if f["disposition"].get("status", "pending") not in ("pending", "not_required")]
    decided_rows = "".join(
        f'<tr><td><a href="#{e(f["id"])}">{e(f["id"])}</a><br>{e(f["title"])}</td><td>{e(f["disposition"]["status"])}</td>'
        f'<td>{e(f["disposition"].get("decided_by"))}</td><td>{e(f["disposition"].get("rationale"))}</td></tr>' for f in decided)
    changes = [r for r in result["rules"] if r["corrected"]]
    change_html = "".join(
        f'<div class="card"><h3>{e(r["id"])} — {e(r["text"])}</h3><pre>{e(yaml.safe_dump({"suggested_logic": r["corrected"]}, sort_keys=False))}</pre>'
        f'<p class="meta">From findings: {", ".join(f"<a href=#{e(x)}>{e(x)}</a>" for x in r["finding_ids"])}</p></div>' for r in changes
    ) or '<p class="meta">No configuration changes proposed.</p>'
    limits = "".join(f"<li>{e(l)}</li>" for l in result["limitations"])
    inputs = " · ".join(f"{e(k.replace('_', ' '))}: <code>{e(v)}</code>" for k, v in result["inputs"].items() if k != "notes")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Assurance · {e(req['id'])}</title><style>{CSS}</style></head>
<body data-req="{e(req['id'])}">
<header class="top"><div class="wrap">
<div class="meta">Screening Assurance · requisition assurance report</div>
<h1>{e(req['title'])} <span class="meta">({e(req['id'])})</span></h1>
<div class="meta">job family <code>{e(req['job_family'])}</code> · knowledge <code>{e(result['knowledge']['fingerprint'])}</code> · engine {e(result['engine_version'])} · run {e(result['run_at'])}</div>
<div class="stats">
<div class="stat"><b>{lv['level_1']}</b><span>demonstrable inconsistencies</span></div>
<div class="stat"><b>{lv['level_2']}</b><span>risks &amp; review opportunities</span></div>
<div class="stat"><b>{s['candidates_surfaced']}<span style="font-size:14px"> / {s['candidates_assessed']}</span></b><span>candidates surfaced for review</span></div>
<div class="stat"><b>{lv['level_3']}</b><span>measured outcomes</span></div>
<div class="stat"><b>{s['pending_decisions']}</b><span>awaiting decision</span></div>
</div>
<nav class="toc"><a href="#s1">1 Requirements</a><a href="#s2">2 Rules</a><a href="#s3">3 Inconsistencies</a><a href="#s4">4 Risks</a><a href="#s5">5 Candidates</a><a href="#s6">6 Changes</a><a href="#s7">7 Decisions</a><a href="#s8">8 Outcomes</a></nav>
</div></header>
<main class="wrap">
<div class="note">This report recommends changes and human review. It does not reject, advance or hire anyone, and it never claims a candidate was wrongly excluded. Level 1 findings are established by the supplied materials; Level 2 findings need human judgement; Level 3 findings are measured outcomes.</div>
<p class="meta">Inputs received: {inputs}</p>
<details open><summary>Limitations of this run</summary><ul>{limits}</ul></details>
<h2 id="s1">1. Requirements and stated intent</h2>
<div class="tbl"><table><thead><tr><th>ID</th><th>Requirement</th><th>Stated</th><th>Proposed classification</th><th>Basis</th></tr></thead><tbody>{req_rows}</tbody></table></div>
<p class="meta">🔒 Protected (legal, licensing or employer non-negotiable): no alternative path is ever proposed.</p>
<h2 id="s2">2. Screening rules inspected</h2>
<div class="tbl"><table><thead><tr><th>Rule</th><th>Rule text</th><th>Linked req.</th><th>Status</th><th>Findings</th></tr></thead><tbody>{rule_rows}</tbody></table></div>
<h2 id="s3">3. Confirmed inconsistencies</h2>{section(("confirmed_inconsistency",))}
<h2 id="s4">4. Potential missed-talent risks</h2>{section(("design_risk", "unverified_assumption", "input_limitation"))}
<h2 id="s5">5. Candidate-review opportunities</h2>{section(("candidate_review_opportunity",))}
<details><summary>Candidates assessed but not surfaced</summary><div class="tbl"><table><thead><tr><th>Candidate</th><th>ATS status</th><th>Excluded by</th><th>Reason</th></tr></thead><tbody>{not_surfaced}</tbody></table></div></details>
{('<details><summary>Protected and suppressed items</summary><ul>' + suppressed + '</ul></details>') if suppressed else ''}
<h2 id="s6">6. Recommended changes</h2>
<p class="meta">Suggested changes for the employer to implement in the ATS. Nothing is applied automatically.</p>{change_html}
<h2 id="s7">7. Human decisions and rationale</h2>
{('<div class="tbl"><table><thead><tr><th>Finding</th><th>Decision</th><th>By</th><th>Rationale</th></tr></thead><tbody>' + decided_rows + '</tbody></table></div>') if decided else '<p class="meta">No decisions recorded yet. Use the controls on each finding, then export <code>decisions.yaml</code> and re-run.</p>'}
<h2 id="s8">8. Outcome measurements</h2>{_measurement_html(result)}
{section(("measured_impact",)) if any(f["category"] == "measured_impact" for f in F) else ""}
{discovery_html}
</main>
<div class="bar"><div class="wrap"><div class="who"><label for="who" class="meta">Reviewer</label><input id="who" placeholder="you@company.com"></div>
<span id="count"></span><button class="ghost" id="show">Preview</button><button id="export">Export decisions.yaml</button></div>
<div class="wrap"><pre id="preview" hidden></pre></div></div>
<script>{JS}</script>
</body></html>
"""


def result_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=False, default=str)
