/* Candidate Rediscovery Workbench — thin presentation layer.
 * All matching, grouping, evidence interpretation and validation happen in the Python engine.
 * This file only fetches results, renders them with textContent (never innerHTML of data),
 * and posts explicit, attributed decisions back to the local server. */
"use strict";

const TOKEN = document.querySelector('meta[name="sa-token"]').content;
const S = { state: null, session: null, run: null, view: "intake", selCandidate: null, selFinding: null,
            levelFilter: "all", validation: null, files: {}, evalOut: null, verify: {} };

// ------------------------------------------------------------------ helpers
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v === null || v === undefined) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "text") el.textContent = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const $ = (id) => document.getElementById(id);
const short = (s, n = 12) => (s ? String(s).slice(0, n) : "");
function reviewer() { return $("reviewer").value.trim(); }
function toast(msg, err) {
  const t = $("toast"); t.textContent = msg; t.className = "toast" + (err ? " err" : ""); t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, err ? 7000 : 3500);
}
async function api(method, path, body) {
  const opts = { method, headers: { "X-SA-Token": TOKEN } };
  if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
  const res = await fetch("/api/" + path, opts);
  const ctype = res.headers.get("Content-Type") || "";
  if (!ctype.includes("application/json")) {
    if (!res.ok) throw new Error("Request failed (" + res.status + ")");
    return res;
  }
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(data.error || "Request failed");
    err.details = data.details || [];
    throw err;
  }
  return data;
}
async function guarded(fn) {
  try { await fn(); } catch (e) {
    toast(e.message + (e.details && e.details.length ? ": " + e.details.slice(0, 3).join("; ") : ""), true);
  }
}
function needReviewer() {
  if (reviewer()) return true;
  toast("Enter your name in Reviewer first. Every decision and run is attributed.", true);
  $("reviewer").focus();
  return false;
}

const GROUPS = {
  direct: ["Direct evidence", "Supplied evidence directly supports every required requirement."],
  transferable: ["Potentially transferable", "Every required requirement is covered; at least one through an alternative path that you need to verify."],
  insufficient: ["Insufficient evidence", "Some required evidence exists, but the record is partial or a mandatory requirement cannot be verified yet."],
  not_surfaced: ["Not surfaced", "A mandatory requirement is not met, or required evidence is missing from a complete record."],
  blocked: ["Not available for action", "Not authorized for rediscovery, authorization expired, or evidence too old. Evidence is not shown."],
  active_workflow: ["Already in active review", "In active review in the ATS; not repeated here."],
};
const STATUS = {
  evidenced: ["Supported", "ok"], alternative_path: ["Supported via alternative path", "ok"],
  insufficient: ["Below stated threshold", "warn"], not_evidenced: ["Not evidenced", "muted"],
  pending_clarification: ["Necessity unconfirmed", "warn"], protected_missing: ["Mandatory credential missing", "bad"],
};
const CAND_DISP = { review_in_ats: "Review in the ATS", request_more_information: "Request more information",
                    not_a_fit_for_this_role: "Not a fit for this role", defer: "Defer" };
const FIND_DISP = { accepted: "Accept", rejected: "Reject", deferred: "Defer", requested_evidence: "Request evidence",
                    confirmed_necessary: "Confirm the requirement is necessary", reclassified_preferred: "Reclassify as preferred",
                    approved_candidate_review: "Approve candidate review" };
const LEVEL = { 1: ["Level 1", "Demonstrable inconsistency", "bad"], 2: ["Level 2", "Missed-talent risk", "warn"], 3: ["Level 3", "Measured impact", "ok"] };
const CONFIG = { ats_export_verified: ["Verified ATS configuration (export)", "ok"], ats_api_verified: ["Verified ATS configuration (API)", "ok"],
                 recruiter_documentation: ["Recruiter documentation, not verified", "warn"], not_supplied: ["No screening configuration supplied", "bad"] };

// ------------------------------------------------------------------ shell
function renderShell() {
  const prov = $("provenance"); prov.replaceChildren();
  const st = S.state;
  if (st) prov.append(h("span", {}, "Engine ", h("b", {}, st.engine_version)));
  if (S.session) prov.append(h("span", {}, "Requisition ", h("b", {}, S.session.requisition_id)));
  if (S.run) prov.append(
    h("span", {}, "Run ", h("b", { class: "mono" }, S.run.run.run_id)),
    h("span", {}, "Knowledge ", h("b", { class: "mono" }, S.run.run.knowledge.fingerprint)));
  const nav = $("steps"); nav.replaceChildren();
  const steps = [["intake", "Requisition intake", true], ["discovery", "Candidate discovery", !!S.run],
                 ["findings", "Screening findings", !!S.run], ["review", "Review and export", !!S.run]];
  steps.forEach(([id, label, enabled], i) => nav.append(h("button", {
    "aria-current": S.view === id ? "page" : false, disabled: !enabled,
    onclick: () => { S.view = id; render(); } }, h("span", { class: "n" }, i + 1), label)));
  nav.append(h("p", { class: "hint" }, S.run ? "Results are for human review. Nothing here contacts, advances or rejects anyone."
                                             : "Load a requisition package and run discovery to unlock the other steps."));
}
function render() {
  renderShell();
  const m = $("main"); m.replaceChildren();
  const views = { intake: viewIntake, discovery: viewDiscovery, findings: viewFindings, review: viewReview };
  m.append(views[S.view]());
}

// ------------------------------------------------------------------ A. intake
function viewIntake() {
  if (!S.session) return intakeStart();
  const s = S.session, sum = s.summary, cfg = CONFIG[sum.screening_configuration] || ["Unknown", "muted"];
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" },
    h("div", { class: "grow" }, h("h2", {}, s.title + " (" + s.requisition_id + ")"),
      h("p", {}, "Check what was supplied before running. The engine only audits configuration it was actually given.")),
    h("button", { class: "btn", onclick: () => { S.session = null; S.run = null; S.view = "intake"; refreshState(); } }, "Close session")));
  if (s.candidate_data_deleted) root.append(h("div", { class: "banner bad" }, "Candidate data for this session was deleted under its retention rule. Create a new session to continue."));

  const rows = Object.entries(S.state.input_kinds).map(([kind, info]) => {
    const got = s.inputs[kind];
    return h("tr", {}, h("td", {}, kindLabel(kind)),
      h("td", {}, got ? h("span", { class: "tag ok" }, "Supplied") : h("span", { class: "tag " + (info.required ? "bad" : "muted") }, info.required ? "Missing" : "Not supplied")),
      h("td", { class: "mono" }, got ? "sha256 " + short(got.sha256) : ""),
      h("td", {}, got ? (got.bytes / 1024).toFixed(1) + " KB" : ""));
  });
  root.append(h("div", { class: "grid2" },
    h("section", { class: "panel" }, h("h3", {}, "Inputs in this session"),
      h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Input"), h("th", {}, "Status"), h("th", {}, "Fingerprint"), h("th", {}, "Size"))), h("tbody", {}, rows))),
      h("dl", { class: "kv mt12" },
        h("dt", {}, "Screening rules"), h("dd", {}, h("span", { class: "tag " + cfg[1] }, cfg[0]), " ", sum.screening_rules + " rule(s)"),
        h("dt", {}, "Current applicants"), h("dd", {}, sum.current_applicants === null ? "Not supplied" : sum.current_applicants + " de-identified record(s), " + sum.candidate_evidence.replace(/_/g, " ")),
        h("dt", {}, "Candidate pool"), h("dd", {}, sum.pool ? sum.pool.records + " record(s) from " + sum.pool.source_system + ", exported " + sum.pool.exported_at : "Not supplied — only applicants to this requisition will be considered"),
        sum.pool && [h("dt", {}, "Permitted uses"), h("dd", {}, sum.pool.permitted_uses.join(", ").replace(/_/g, " ")),
                     h("dt", {}, "Evidence age limit"), h("dd", {}, sum.pool.max_evidence_age_days + " days")],
        h("dt", {}, "Outcome data"), h("dd", {}, sum.outcomes ? "Supplied (measured results will be shown separately from estimates)" : "Not supplied"),
        h("dt", {}, "Retention"), h("dd", {}, s.retention.delete_after ? "Candidate data is deleted from this computer after " + s.retention.delete_after.slice(0, 10) : "No candidate data in this session"))),
    runPanel(s)));

  root.append(h("section", { class: "panel" }, h("h3", {}, "Requirements"),
    h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "ID"), h("th", {}, "Requirement"), h("th", {}, "Stated as"), h("th", {}, "Alternatives accepted"), h("th", {}, "Rationale on file"))),
      h("tbody", {}, s.requisition.requirements.map(r => h("tr", {}, h("td", {}, h("b", {}, r.id)), h("td", {}, r.text), h("td", {}, r.stated_as),
        h("td", {}, r.accepts_equivalent ? "Yes" : "Not stated"), h("td", {}, r.necessity_rationale || (r.linked_objectives ? "Linked to " + r.linked_objectives.join(", ") : "None")))))))));
  root.append(h("div", { class: "grid2" },
    h("section", { class: "panel" }, h("h3", {}, "Screening rules supplied"),
      h("div", { class: "tbl" }, h("table", {}, h("tbody", {}, s.requisition.screening_rules.map(r => h("tr", {}, h("td", {}, h("b", {}, r.id)), h("td", {}, r.text, h("div", { class: "sub" }, r.type.replace(/_/g, " ") + ", action: " + r.action + (r.linked_requirement ? ", linked to " + r.linked_requirement : ", not linked to a posted requirement")))))))),
      h("p", { class: "sub mt8" }, cfg[0] + ".")),
    h("section", { class: "panel" }, h("h3", {}, "Employer policy (" + s.policy.employer_name + ", " + s.policy.policy_version + ")"),
      h("h4", {}, "Non-negotiable"), listOrNone(s.policy.non_negotiable.map(n => n.concept + " (" + n.basis + (n.job_families ? "; applies to " + n.job_families.join(", ") : "") + "): " + n.rationale)),
      h("h4", { class: "mt10" }, "Equivalencies accepted"), listOrNone(s.policy.accepted_equivalencies.map(a => a.id + " — " + a.approved_by)),
      h("h4", { class: "mt10" }, "Equivalencies rejected"), listOrNone(s.policy.rejected_equivalencies.map(a => a.id + " — " + a.rationale)))));
  return root;
}
function listOrNone(items) { return items.length ? h("ul", { class: "plain small" }, items.map(i => h("li", {}, i))) : h("p", { class: "sub" }, "None"); }
function kindLabel(k) { return { requisition: "Requisition and screening rules", policy: "Employer policy", candidates: "Current applicants", candidate_pool: "Authorized candidate pool", outcomes: "Observed outcomes" }[k] || k; }

function runPanel(s) {
  const sel = h("select", { id: "knowledgeSel" }, S.state.knowledge.map(k => h("option", { value: k.spec, disabled: !k.fingerprint }, k.label + (k.fingerprint ? " — " + k.fingerprint : ""))));
  const last = s.runs.length ? s.runs[s.runs.length - 1] : null;
  if (last) sel.value = last.knowledge.spec;
  const btn = h("button", { class: "btn primary", disabled: !!s.candidate_data_deleted, onclick: () => guarded(async () => {
    if (!needReviewer()) return;
    btn.disabled = true; btn.textContent = "Running…";
    try {
      const run = await api("POST", "sessions/" + s.id + "/runs", { knowledge: sel.value, actor: reviewer() });
      await openSession(s.id, run.run_id);
      S.view = "discovery"; render();
      const co = run.carried_over;
      toast("Run complete. " + (co.finding_decisions_applied.length + co.candidate_decisions_applied.length) + " prior decision(s) carried over.");
    } finally { btn.disabled = false; btn.textContent = "Run discovery and diagnostics"; }
  }) }, "Run discovery and diagnostics");
  return h("section", { class: "panel" }, h("h3", {}, "Run"),
    h("label", { class: "field" }, "Knowledge revision", sel),
    h("p", { class: "sub mt8" }, "The exact knowledge documents used are copied into the run, so its results can be reproduced later even if the knowledge changes."),
    h("div", { class: "row mt10" }, btn),
    s.runs.length ? h("div", { class: "mt14" }, h("h4", {}, "Previous runs"), h("ul", { class: "plain small" },
      s.runs.slice().reverse().map(r => h("li", {}, h("a", { href: "#", onclick: (e) => { e.preventDefault(); guarded(async () => { await openSession(s.id, r.run_id); S.view = "discovery"; render(); }); } }, r.run_id),
        " " + r.run_at.slice(0, 16).replace("T", " ") + ", " + r.knowledge.fingerprint)))) : null);
}

function intakeStart() {
  const st = S.state;
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Start with a requisition"),
    h("p", {}, "Load an included example or your own package. Inputs are validated against the data contracts and copied into a workspace on this computer."))));
  const incl = h("input", { type: "checkbox", id: "inclOutcomes", checked: true });
  const ex = h("section", { class: "panel" }, h("h3", {}, "Included examples"),
    h("div", { class: "tbl" }, h("table", {}, h("tbody", {}, st.examples.map(e => h("tr", {},
      h("td", {}, h("b", {}, e.id), h("div", { class: "sub" }, e.title)),
      h("td", { class: "small" }, (e.files.length ? e.files.map(kindLabel).join(", ") : "Requisition only"), h("div", { class: "sub" }, (CONFIG[e.screening_configuration] || ["", ""])[0])),
      h("td", {}, h("button", { class: "btn" + (e.id === "REQ-SRE-0142" ? " primary" : ""), onclick: () => guarded(async () => {
        if (!needReviewer()) return;
        const meta = await api("POST", "sessions", { example: e.id, include_outcomes: incl.checked, actor: reviewer() });
        await openSession(meta.id); render(); toast("Loaded " + e.id + " into a new session.");
      }) }, "Load"))))))),
    h("label", { class: "row small mt10" }, incl, "Include the example's recorded outcomes"));

  const fileRows = Object.entries(st.input_kinds).map(([kind, info]) => {
    const input = h("input", { type: "file", accept: ".yaml,.yml,.json", "aria-label": kindLabel(kind), onchange: (ev) => readFile(kind, ev.target.files[0]) });
    const res = S.validation && S.validation.report.find(r => r.kind === kind);
    return h("tr", {}, h("td", {}, kindLabel(kind), h("div", { class: "sub" }, info.required ? "Required" : "Optional")),
      h("td", {}, input, S.files[kind] ? h("div", { class: "sub" }, S.files[kind].name) : null),
      h("td", {}, res ? statusTag(res) : null, res && res.errors.length ? h("ul", { class: "plain small" }, res.errors.map(x => h("li", {}, x))) : null,
        res && res.notes ? h("ul", { class: "plain small" }, res.notes.map(x => h("li", {}, x))) : null));
  });
  const up = h("section", { class: "panel" }, h("h3", {}, "Your own package"),
    h("p", { class: "sub" }, "YAML or JSON files up to " + (st.max_file_bytes / 1048576) + " MB each. Candidate files must be de-identified: names, contact details and protected characteristics are rejected."),
    h("div", { class: "tbl" }, h("table", {}, h("tbody", {}, fileRows))),
    S.validation ? h("div", { class: "banner " + (S.validation.ok ? "info" : "bad"), class: "mt10" },
      S.validation.ok ? "All supplied inputs are valid. Screening rules: " + S.validation.summary.screening_configuration_label + "." : "Fix the inputs marked invalid or missing, then validate again.") : null,
    h("div", { class: "row mt12" },
      h("button", { class: "btn", onclick: () => guarded(async () => { S.validation = await api("POST", "validate", { files: fileTexts() }); render(); }) }, "Validate inputs"),
      h("button", { class: "btn primary", disabled: !(S.validation && S.validation.ok), onclick: () => guarded(async () => {
        if (!needReviewer()) return;
        const meta = await api("POST", "sessions", { files: fileTexts(), actor: reviewer() });
        S.files = {}; S.validation = null; await openSession(meta.id); render();
      }) }, "Create session")));

  root.append(h("div", { class: "grid2" }, ex, up));
  if (st.sessions.length) root.append(h("section", { class: "panel" }, h("h3", {}, "Sessions on this computer"),
    h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Session"), h("th", {}, "Requisition"), h("th", {}, "Created"), h("th", {}, "Candidate data deleted after"), h("th", {}, ""))),
      h("tbody", {}, st.sessions.map(x => h("tr", {}, h("td", { class: "mono" }, x.id), h("td", {}, x.requisition_id + " " + x.title), h("td", {}, x.created_at.slice(0, 16).replace("T", " ")),
        h("td", {}, x.candidate_data_deleted ? "Deleted" : (x.retention.delete_after || "—").slice(0, 10)),
        h("td", {}, h("div", { class: "row" }, h("button", { class: "btn", onclick: () => guarded(async () => { await openSession(x.id); render(); }) }, "Open"),
          h("button", { class: "btn danger", onclick: () => guarded(async () => {
            if (!needReviewer() || !confirm("Delete session " + x.id + " and all its candidate data from this computer?")) return;
            await api("DELETE", "sessions/" + x.id, { actor: reviewer(), reason: "deleted by reviewer" });
            await refreshState(); toast("Session deleted.");
          }) }, "Delete"))))))))));
  return root;
}
function statusTag(r) {
  const m = { valid: ["Valid", "ok"], invalid: ["Invalid", "bad"], missing: ["Missing", "bad"], not_supplied: ["Not supplied", "muted"] }[r.status];
  return h("span", { class: "tag " + m[1] }, m[0]);
}
function readFile(kind, file) {
  if (!file) { delete S.files[kind]; return; }
  if (file.size > S.state.max_file_bytes) { toast(file.name + " is larger than the limit.", true); return; }
  const fr = new FileReader();
  fr.onload = () => { S.files[kind] = { name: file.name, text: String(fr.result) }; S.validation = null; render(); };
  fr.readAsText(file);
}
function fileTexts() { const o = {}; for (const [k, v] of Object.entries(S.files)) o[k] = v.text; return o; }

// ------------------------------------------------------------------ B. discovery
function candDecision(id) { return (S.session.review_decisions || []).find(d => d.candidate_id === id); }
function viewDiscovery() {
  const d = S.run.discovery, c = d.counts;
  const root = h("div", {});
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Candidate discovery"),
    h("p", {}, "Grouped by what the supplied evidence supports. There is no ranking or score, and appearing here does not mean a person is qualified."))));
  root.append(h("div", { class: "counts" }, ["direct", "transferable", "insufficient", "not_surfaced", "blocked", "active_workflow"].map(g =>
    h("div", {}, h("b", {}, c[g]), h("span", {}, GROUPS[g][0])))));
  d.limitations.forEach(l => root.append(h("p", { class: "sub" }, l)));

  const list = h("div", { class: "list", role: "listbox", "aria-label": "Candidates" });
  for (const g of ["direct", "transferable", "insufficient"]) {
    const items = d.entries.filter(e => e.group === g);
    list.append(h("div", { class: "group-head" }, h("h4", {}, GROUPS[g][0], h("span", { class: "sub" }, items.length)), h("p", {}, GROUPS[g][1])));
    items.forEach(e => list.append(candidateItem(e)));
  }
  const split = h("div", { class: "split mt14" }, list, h("div", { class: "detail" }, candidateDetail()));
  root.append(split);

  const listed = d.entries.filter(e => (e.group === "not_surfaced" || e.group === "blocked") && e.listable);
  const unlisted = d.entries.filter(e => e.group === "not_surfaced" && !e.listable).length;
  root.append(h("section", { class: "panel mt18" }, h("h3", {}, "Not surfaced or not available for action"),
    h("p", { class: "sub" }, "Only dispositions the supplied data can explain are listed. " + unlisted + " record(s) with no evidence for any required requirement are counted, not listed. " + c.active_workflow + " already in active review."),
    listed.length ? h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Candidate"), h("th", {}, "Source record"), h("th", {}, "Group"), h("th", {}, "Reason"))),
      h("tbody", {}, listed.map(e => h("tr", {}, h("td", {}, h("b", {}, e.candidate_id)), h("td", { class: "mono" }, e.source.record_ref),
        h("td", {}, h("span", { class: "tag " + (e.group === "blocked" ? "muted" : "outline") }, GROUPS[e.group][0])), h("td", {}, e.reason)))))) : h("p", {}, "None.")));
  return root;
}
function reqTags(e) {
  return e.requirements.filter(r => r.stated_as === "required").map(r => {
    const st = STATUS[r.status] || [r.status, "muted"];
    const issue = e.mandatory_issues.find(m => m.requirement === r.id);
    const label = issue && issue.issue === "cannot_verify" ? "cannot verify" : st[0].toLowerCase();
    return h("span", { class: "tag " + (issue && issue.issue === "cannot_verify" ? "warn" : st[1]) }, r.id + " " + label);
  });
}
function candidateItem(e) {
  const dec = candDecision(e.candidate_id);
  return h("button", { class: "item", role: "option", "aria-selected": S.selCandidate === e.candidate_id ? "true" : "false",
    onclick: () => { S.selCandidate = e.candidate_id; render(); } },
    h("div", { class: "line1" }, h("span", { class: "id" }, e.candidate_id), h("span", { class: "src" }, e.source.kind === "candidate_pool" ? "Pool record" : "Applied to this role")),
    h("div", { class: "tags" }, reqTags(e), dec ? h("span", { class: "tag accent" }, CAND_DISP[dec.disposition]) : h("span", { class: "tag outline" }, "Decision pending")));
}
function candidateDetail() {
  const d = S.run.discovery;
  const e = d.entries.find(x => x.candidate_id === S.selCandidate);
  if (!e || !["direct", "transferable", "insufficient"].includes(e.group)) return h("div", { class: "panel empty" }, "Select a candidate to see why they appeared, the evidence, and what remains unknown.");
  const p = h("div", { class: "panel detail-body" });
  p.append(h("div", { class: "detail-head" }, h("div", {}, h("h2", {}, e.candidate_id), h("div", { class: "sub mono" }, e.source.system + " / " + e.source.record_ref)),
    h("span", { class: "tag " + (e.group === "direct" ? "ok" : "warn") }, GROUPS[e.group][0])));
  p.append(h("div", { class: "section" }, h("h4", {}, "Why this person appeared"), h("ul", { class: "plain" }, e.why.map(w => h("li", {}, w)))));
  p.append(h("div", { class: "section" }, h("h4", {}, "Evidence by requirement"), ledger(e.requirements)));
  const unknown = e.mandatory_issues.map(m => h("li", {}, h("b", {}, m.requirement + " "), h("span", { class: "tag " + (m.issue === "not_satisfied" ? "bad" : "warn") }, m.issue.replace(/_/g, " ")), " " + m.detail))
    .concat(e.unverified.map(u => h("li", {}, h("b", {}, u.requirement + " "), u.reason)));
  p.append(h("div", { class: "section" }, h("h4", {}, "What remains unknown"),
    h("ul", { class: "plain" }, unknown.length ? unknown : [h("li", {}, "Nothing flagged by the engine.")], h("li", {}, "Qualification itself has not been established; this is a request for human review."))));
  if (e.verify_next.length) p.append(h("div", { class: "section" }, h("h4", {}, "What to verify next"), h("ul", { class: "plain" }, e.verify_next.map(v => h("li", {}, v)))));
  const sc = e.screening;
  p.append(h("div", { class: "section" }, h("h4", {}, "Supplied screening rules"),
    sc.applied_to_requisition ? h("div", {},
      sc.excluded_by.length ? h("ul", { class: "plain" }, sc.excluded_by.map(x => h("li", {}, h("b", {}, x.rule), " — " + x.reason))) : h("p", {}, sc.note || "Not excluded by any supplied rule."),
      h("p", { class: "sub" }, "Exclusion " + sc.basis + (sc.established ? "." : "; treat as indicative.")),
      sc.recorded_rule ? h("p", { class: "sub" }, "The ATS recorded rule " + sc.recorded_rule + " as the exclusion reason.") : null,
      sc.related_findings.length ? h("p", { class: "sub" }, "Related finding: ", sc.related_findings.map(f => findingLink(f))) : null)
    : h("p", {}, sc.basis)));
  p.append(h("div", { class: "section" }, h("h4", {}, "Record and constraints"), h("dl", { class: "kv" },
    h("dt", {}, "Evidence source"), h("dd", {}, (e.source.evidence_provenance || "").replace(/_/g, " ")),
    h("dt", {}, "Evidence updated"), h("dd", {}, e.freshness.evidence_updated_at ? e.freshness.evidence_updated_at + " (" + e.freshness.age_days + " days before assessment, limit " + e.freshness.max_age_days + ")" : e.freshness.note || "—"),
    e.prior_applications.length ? [h("dt", {}, "Prior applications"), h("dd", {}, h("ul", { class: "plain" }, e.prior_applications.map(a => h("li", {}, a.requisition_ref + (a.role_title ? " " + a.role_title : "") + ", " + a.applied_at + ", " + a.outcome.replace(/_/g, " ") + (a.recorded_reason ? " (" + a.recorded_reason + ")" : "")))))] : null,
    h("dt", {}, "Constraints"), h("dd", {}, h("ul", { class: "plain" }, e.constraints.map(x => h("li", {}, x)))),
    h("dt", {}, "Run reference"), h("dd", { class: "mono" }, S.run.run.run_id + ", " + d.knowledge + ", assessed as of " + d.as_of))));
  p.append(candidateDecisionBox(e));
  return p;
}
function ledger(reqs) {
  return h("div", { class: "ledger" }, reqs.map(r => {
    const st = STATUS[r.status] || [r.status, "muted"];
    return h("div", { class: "ledger-row s-" + r.status }, h("div", { class: "bar" }),
      h("div", { class: "rid" }, r.id, h("small", {}, r.stated_as)),
      h("div", { class: "body" },
        h("div", { class: "req" }, h("span", {}, r.text), h("span", { class: "tags" }, h("span", { class: "tag " + st[1] }, st[0]), r.protected ? h("span", { class: "tag bad" }, "Mandatory by law or policy") : null)),
        r.path_label ? h("div", { class: "note" }, "How: " + r.path_label + (r.months !== null && r.months !== undefined ? ", " + r.months + " relevant months" : "")) : null,
        r.evidence.slice(0, 3).map(ev => h("blockquote", { class: "quote" }, h("span", { class: "where" }, ev.source), ev.text)),
        r.notes.map(n => h("div", { class: "note" }, n))));
  }));
}
function candidateDecisionBox(e) {
  const dec = candDecision(e.candidate_id);
  const sel = h("select", {}, h("option", { value: "" }, "Choose what to do next"), S.state.candidate_dispositions.map(k => h("option", { value: k }, CAND_DISP[k] || k)));
  const why = h("textarea", { placeholder: "Rationale (required). Do not paste contact details." });
  const mins = h("input", { type: "number", min: "0", step: "1", placeholder: "optional" });
  return h("div", { class: "decision" }, h("h4", {}, "Your decision"),
    dec ? h("p", { class: "recorded" }, h("span", { class: "tag accent" }, CAND_DISP[dec.disposition]), " by " + dec.decided_by + " on " + dec.decided_at.slice(0, 10) + ": " + dec.rationale) : null,
    h("div", { class: "row" }, h("label", { class: "field" }, "Next step", sel), h("label", { class: "field w160" }, "Review minutes", mins)),
    h("label", { class: "field mt8" }, "Rationale", why),
    h("div", { class: "row mt10" }, h("button", { class: "btn primary", onclick: () => guarded(async () => {
      if (!needReviewer()) return;
      if (!sel.value) throw new Error("Choose a next step");
      await api("POST", "sessions/" + S.session.id + "/runs/" + S.run.run.run_id + "/candidate-decisions",
        { candidate_id: e.candidate_id, disposition: sel.value, rationale: why.value, actor: reviewer(), review_minutes: mins.value || null });
      await reloadSession(); render(); toast("Decision recorded for " + e.candidate_id + ".");
    }) }, dec ? "Update decision" : "Record decision")),
    h("p", { class: "sub mt8" }, "Recorded in this workspace only. Nothing is sent to the ATS or the candidate."));
}

// ------------------------------------------------------------------ C. findings
function findingDecision(id) { return (S.session.decisions || []).find(d => d.finding_id === id); }
function findingLink(fid) { return h("a", { href: "#", onclick: (ev) => { ev.preventDefault(); S.selFinding = fid; S.view = "findings"; render(); } }, fid); }
function viewFindings() {
  const r = S.run.result;
  const root = h("div", {});
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Screening findings"),
    h("p", {}, "Where the supplied rules disagree with the posting, or may exclude people who could meet it. Corrections are simulated, never applied to the ATS."))));
  const lv = r.summary.by_level;
  root.append(h("div", { class: "filters", role: "group", "aria-label": "Filter by evidence level" },
    [["all", "All (" + r.findings.length + ")"], ["1", "Level 1 (" + lv.level_1 + ")"], ["2", "Level 2 (" + lv.level_2 + ")"], ["3", "Level 3 (" + lv.level_3 + ")"]].map(([k, label]) =>
      h("button", { "aria-pressed": S.levelFilter === k ? "true" : "false", onclick: () => { S.levelFilter = k; render(); } }, label))));
  const items = r.findings.filter(f => S.levelFilter === "all" || String(f.evidence_level) === S.levelFilter);
  const list = h("div", { class: "list" }, items.map(f => {
    const dec = findingDecision(f.id);
    return h("button", { class: "item", "aria-selected": S.selFinding === f.id ? "true" : "false", onclick: () => { S.selFinding = f.id; render(); } },
      h("div", { class: "line1" }, h("span", { class: "id" }, f.rule_id || f.requirement_id || f.candidate_id || "Run"), h("span", { class: "src" }, LEVEL[f.evidence_level][0])),
      h("div", { class: "small" }, f.title),
      h("div", { class: "tags" }, h("span", { class: "tag " + LEVEL[f.evidence_level][2] }, LEVEL[f.evidence_level][1]),
        f.category === "measured_impact" ? null : dec ? h("span", { class: "tag accent" }, FIND_DISP[dec.disposition] || dec.disposition) : h("span", { class: "tag outline" }, "Decision pending")));
  }));
  root.append(h("div", { class: "split" }, list, h("div", { class: "detail" }, findingDetail())));
  return root;
}
function findingDetail() {
  const r = S.run.result, f = r.findings.find(x => x.id === S.selFinding);
  if (!f) return h("div", { class: "panel empty" }, "Select a finding to see the rule, the evidence, and the decision it needs.");
  const req = S.session.requisition;
  const reqObj = f.requirement_id && req.requirements.find(x => x.id === f.requirement_id);
  const ruleObj = f.rule_id && req.screening_rules.find(x => x.id === f.rule_id);
  const p = h("div", { class: "panel detail-body" });
  p.append(h("div", { class: "detail-head" }, h("div", {}, h("h2", { class: "fs19" }, f.title), h("div", { class: "sub mono" }, f.id)),
    h("div", { class: "tags" }, h("span", { class: "tag " + LEVEL[f.evidence_level][2] }, LEVEL[f.evidence_level][0] + ": " + LEVEL[f.evidence_level][1]), h("span", { class: "tag outline" }, "Confidence " + f.confidence))));
  p.append(h("p", {}, f.observation));
  if (reqObj || ruleObj) p.append(h("div", { class: "section" }, h("h4", {}, "Requirement and supplied rule"), h("dl", { class: "kv" },
    reqObj ? [h("dt", {}, "Requirement " + reqObj.id), h("dd", {}, reqObj.text + " (" + reqObj.stated_as + ")")] : null,
    ruleObj ? [h("dt", {}, "Rule " + ruleObj.id), h("dd", {}, ruleObj.text + " (" + ruleObj.type.replace(/_/g, " ") + ", " + ruleObj.action + ")")] : null)));
  if (f.evidence.length) p.append(h("div", { class: "section" }, h("h4", {}, "Evidence"), f.evidence.slice(0, 8).map(ev => h("blockquote", { class: "quote" }, h("span", { class: "where" }, (ev.requirement ? ev.requirement + " " : "") + ev.source), ev.text))));
  const aff = f.affected_candidates || [], unl = f.unlocked_candidates || [];
  if (aff.length || unl.length) p.append(h("div", { class: "section" }, h("h4", {}, "Affected candidates in the supplied data"),
    h("p", {}, aff.length ? ["This correction alone lets ", aff.map((c, i) => [i ? ", " : "", candLink(c)]), " pass the rule."] : "No single candidate passes the rule on this correction alone."),
    unl.length ? h("p", {}, "Candidate-review opportunities depending on it: ", unl.map((c, i) => [i ? ", " : "", candLink(c)])) : null));
  if (f.category !== "measured_impact") p.append(h("div", { class: "section" }, h("h4", {}, "Proposed action"), h("dl", { class: "kv" },
    h("dt", {}, "Action"), h("dd", {}, f.proposed_action), h("dt", {}, "Expected benefit"), h("dd", {}, f.expected_benefit), h("dt", {}, "Trade-off"), h("dd", {}, f.tradeoffs)),
    f.proposed_change ? h("details", { class: "mt8" }, h("summary", {}, "Suggested configuration change (simulation only)"), h("pre", { class: "out" }, JSON.stringify(f.proposed_change, null, 2))) : null));
  if (f.limitations.length) p.append(h("div", { class: "section" }, h("h4", {}, "Limitations"), h("ul", { class: "plain small" }, f.limitations.map(l => h("li", {}, l)))));
  p.append(h("p", { class: "sub mono mt14" }, "Knowledge " + f.knowledge_version + (f.knowledge_refs.length ? ", records " + f.knowledge_refs.join(", ") : "") + ". Sources: " + f.source_refs.map(s => s.kind + ":" + s.id).join(", ")));
  if (f.allowed_dispositions && f.allowed_dispositions.length) p.append(findingDecisionBox(f));
  return p;
}
function candLink(cid) {
  const e = S.run.discovery.entries.find(x => x.candidate_id === cid);
  if (!e || !["direct", "transferable", "insufficient"].includes(e.group)) return h("span", {}, cid);
  return h("a", { href: "#", onclick: (ev) => { ev.preventDefault(); S.selCandidate = cid; S.view = "discovery"; render(); } }, cid);
}
function findingDecisionBox(f) {
  const dec = findingDecision(f.id);
  const applied = f.disposition && f.disposition.status !== "pending";
  const sel = h("select", {}, h("option", { value: "" }, "Choose a decision"), f.allowed_dispositions.map(k => h("option", { value: k }, FIND_DISP[k] || k)));
  const why = h("textarea", { placeholder: "Rationale (required)" });
  return h("div", { class: "decision" }, h("h4", {}, "Decision"),
    dec ? h("p", { class: "recorded" }, h("span", { class: "tag accent" }, FIND_DISP[dec.disposition] || dec.disposition), " by " + dec.decided_by + " on " + dec.decided_at.slice(0, 10) + ": " + dec.rationale,
      applied ? null : h("span", { class: "sub" }, " — takes effect on the next run.")) : null,
    h("label", { class: "field" }, "Decision", sel), h("label", { class: "field mt8" }, "Rationale", why),
    h("div", { class: "row mt10" }, h("button", { class: "btn primary", onclick: () => guarded(async () => {
      if (!needReviewer()) return;
      if (!sel.value) throw new Error("Choose a decision");
      await api("POST", "sessions/" + S.session.id + "/runs/" + S.run.run.run_id + "/finding-decisions",
        { finding_id: f.id, disposition: sel.value, rationale: why.value, actor: reviewer() });
      await reloadSession(); render(); toast("Decision recorded. Re-run to apply it to the analysis and report.");
    }) }, dec ? "Update decision" : "Record decision")),
    h("p", { class: "sub mt8" }, "Rejecting a finding withdraws its correction from the next run. Nothing is changed in the ATS."));
}

// ------------------------------------------------------------------ D. review and export
function viewReview() {
  const s = S.session, run = S.run.run, r = S.run.result, d = S.run.discovery;
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Review and export"),
    h("p", {}, "Decisions are kept in this session and carried into later runs while their findings and candidates still exist."))));
  const actionable = d.entries.filter(e => ["direct", "transferable", "insufficient"].includes(e.group));
  const pendingC = actionable.filter(e => !candDecision(e.candidate_id)).length;
  const decidable = r.findings.filter(f => (f.allowed_dispositions || []).length);
  const pendingF = decidable.filter(f => !findingDecision(f.id)).length;
  const newSince = s.decisions.filter(x => x.decided_at > run.run_at).length + s.review_decisions.filter(x => x.decided_at > run.run_at).length;
  root.append(h("div", { class: "counts" },
    h("div", {}, h("b", {}, pendingC), h("span", {}, "candidates awaiting a decision")),
    h("div", {}, h("b", {}, pendingF), h("span", {}, "findings awaiting a decision")),
    h("div", {}, h("b", {}, newSince), h("span", {}, "decisions recorded after this run"))));
  if (newSince) root.append(h("div", { class: "banner info" }, newSince + " decision(s) were recorded after this run. Re-run to include them in the analysis and the exported report. ",
    h("button", { class: "btn", onclick: () => guarded(async () => {
      if (!needReviewer()) return;
      const nr = await api("POST", "sessions/" + s.id + "/runs", { knowledge: run.knowledge.spec, actor: reviewer() });
      await openSession(s.id, nr.run_id); render();
      toast("New run " + nr.run_id + ": " + nr.carried_over.finding_decisions_applied.length + " finding and " + nr.carried_over.candidate_decisions_applied.length + " candidate decision(s) carried over" +
        (nr.carried_over.finding_decisions_stale.length + nr.carried_over.candidate_decisions_stale.length ? "; some no longer apply (see below)." : "."));
    }) }, "Re-run with the same knowledge")));

  const co = run.carried_over;
  if (co.finding_decisions_stale.length || co.candidate_decisions_stale.length) root.append(h("div", { class: "banner" },
    "Decisions kept but not applied to this run because their finding or candidate no longer appears: " + co.finding_decisions_stale.concat(co.candidate_decisions_stale).join(", ")));

  const exportsList = [["review-list.csv", "Candidate review list (CSV)"], ["review-list.yaml", "Candidate review list (YAML)"], ["report.md", "Report (Markdown)"],
    ["report.html", "Report (HTML)"], ["findings.json", "Findings (JSON)"], ["discovery.json", "Discovery (JSON)"], ["decisions.yaml", "Finding decisions"],
    ["review-decisions.yaml", "Candidate decisions"], ["changes.yaml", "Accepted configuration changes"], ["bundle.zip", "Everything, with knowledge snapshot (ZIP)"]];
  root.append(h("div", { class: "grid2" },
    h("section", { class: "panel" }, h("h3", {}, "Export"), h("p", { class: "sub" }, "Exports reflect run " + run.run_id + ". Decision files reflect everything recorded so far."),
      h("div", { class: "row" }, exportsList.map(([name, label]) => h("button", { class: "btn" + (name === "review-list.csv" ? " primary" : ""), onclick: () => guarded(() => download(name)) }, label)))),
    h("section", { class: "panel" }, h("h3", {}, "Outcomes"), outcomes(r.measurement))));

  root.append(h("section", { class: "panel" }, h("h3", {}, "Candidate decisions"), decisionsTable(s.review_decisions.map(x => [x.candidate_id, CAND_DISP[x.disposition] || x.disposition, x.decided_by, x.decided_at.slice(0, 16).replace("T", " "), x.review_minutes ?? "", x.rationale]),
    ["Candidate", "Next step", "By", "When", "Minutes", "Rationale"])));
  root.append(h("section", { class: "panel" }, h("h3", {}, "Finding decisions"), decisionsTable(s.decisions.map(x => [x.finding_id, FIND_DISP[x.disposition] || x.disposition, x.decided_by, x.decided_at.slice(0, 16).replace("T", " "), x.rationale]),
    ["Finding", "Decision", "By", "When", "Rationale"])));

  root.append(h("section", { class: "panel" }, h("h3", {}, "Runs and reproducibility"),
    h("p", { class: "sub" }, "Each run stores input fingerprints, the knowledge documents used and the decisions applied. Verifying re-runs it from those and compares the outputs byte for byte."),
    h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Run"), h("th", {}, "When"), h("th", {}, "Knowledge"), h("th", {}, "Inputs"), h("th", {}, ""))),
      h("tbody", {}, s.runs.slice().reverse().map(x => {
        const v = S.verify[x.run_id];
        return h("tr", {}, h("td", { class: "mono" }, x.run_id), h("td", {}, x.run_at.slice(0, 16).replace("T", " ") + " by " + x.run_by),
          h("td", { class: "mono" }, x.knowledge.fingerprint), h("td", { class: "mono" }, Object.entries(x.inputs).map(([k, v2]) => h("div", {}, k + " " + short(v2, 10)))),
          h("td", {}, h("button", { class: "btn", onclick: () => guarded(async () => {
            if (!needReviewer()) return;
            S.verify[x.run_id] = await api("POST", "sessions/" + s.id + "/runs/" + x.run_id + "/verify", { actor: reviewer() }); render();
          }) }, "Verify"), v ? h("div", { class: "mt6" }, h("span", { class: "tag " + (v.reproduced ? "ok" : "bad") }, v.reproduced ? "Reproduced exactly" : "Not reproduced"),
            h("ul", { class: "plain small" }, v.checks.filter(c => !c.ok).map(c => h("li", {}, c.check + (c.detail ? ": " + c.detail : ""))))) : null));
      }))))));

  if (S.state.evaluation_available) root.append(evaluationPanel());
  return root;
}
function decisionsTable(rows, head) {
  if (!rows.length) return h("p", { class: "sub" }, "None recorded yet.");
  return h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, head.map(x => h("th", {}, x)))), h("tbody", {}, rows.map(r => h("tr", {}, r.map(c => h("td", {}, String(c))))))));
}
function outcomes(m) {
  if (!m) return h("p", { class: "sub" }, "No outcome data supplied. Measured results appear here once an outcomes file with a documented baseline is included.");
  const me = m.measured;
  return h("div", {},
    h("p", { class: "sub" }, "Comparison method: " + m.comparison_method),
    h("h4", {}, "Measured"),
    h("dl", { class: "kv" }, h("dt", {}, "Additional reviews"), h("dd", {}, me.additional_reviews), h("dt", {}, "Confirmed to meet requirements"), h("dd", {}, me.confirmed_meets_requirements),
      h("dt", {}, "Confirmed not to meet"), h("dd", {}, me.confirmed_does_not_meet), h("dt", {}, "Insufficient evidence"), h("dd", {}, me.insufficient_evidence),
      h("dt", {}, "Recruiter minutes"), h("dd", {}, me.review_minutes), h("dt", {}, "Qualified per recruiter hour"), h("dd", {}, me.incremental_qualified_per_recruiter_hour ?? "—")),
    m.estimated ? h("div", { class: "banner mt10" }, h("b", {}, "Estimated, not observed. "),
      Object.entries(m.estimated).filter(([k]) => k !== "label" && k !== "assumptions").map(([k, v]) => k.replace(/_/g, " ") + ": " + v).join("; ") + ". Assumptions source: " + (m.estimated.assumptions.source || "not stated") + ".") : null,
    h("p", { class: "sub mt8" }, m.attribution_note));
}
function evaluationPanel() {
  const opts = () => S.state.knowledge.filter(k => k.fingerprint).map(k => h("option", { value: k.spec }, k.label));
  const cand = h("select", {}, opts()); cand.value = "pack";
  const base = h("select", {}, opts());
  return h("section", { class: "panel" }, h("h3", {}, "Knowledge and evaluation"),
    h("p", { class: "sub" }, "For knowledge administrators: after editing a knowledge document, run the labeled evaluation suite and compare against the version in use. Fixture results are synthetic and are not a measure of real-world accuracy."),
    h("div", { class: "row" }, h("label", { class: "field" }, "Knowledge to evaluate", cand), h("label", { class: "field" }, "Compare against", base)),
    h("div", { class: "row mt10" },
      h("button", { class: "btn", onclick: () => guarded(async () => { S.evalOut = await api("POST", "evaluate", { knowledge: cand.value }); render(); }) }, "Run evaluation"),
      h("button", { class: "btn", onclick: () => guarded(async () => { S.evalOut = await api("POST", "compare", { baseline: base.value, candidate: cand.value }); render(); }) }, "Compare")),
    S.evalOut ? h("div", { class: "mt12" }, h("span", { class: "tag " + (S.evalOut.passed ? "ok" : "bad") }, S.evalOut.passed ? "Gate passed" : "Gate failed"), h("pre", { class: "out" }, S.evalOut.markdown)) : null);
}
async function download(name) {
  const res = await api("GET", "sessions/" + S.session.id + "/runs/" + S.run.run.run_id + "/export/" + name);
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename="([^"]+)"/);
  const a = h("a", { href: URL.createObjectURL(blob), download: m ? m[1] : name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  toast("Exported " + (m ? m[1] : name) + ".");
}

// ------------------------------------------------------------------ data
async function refreshState() { S.state = await api("GET", "state"); render(); }
async function reloadSession() { S.session = await api("GET", "sessions/" + S.session.id); }
async function openSession(id, runId) {
  S.session = await api("GET", "sessions/" + id);
  const rid = runId || (S.session.runs.length ? S.session.runs[S.session.runs.length - 1].run_id : null);
  S.run = rid ? await api("GET", "sessions/" + id + "/runs/" + rid) : null;
  S.state = await api("GET", "state");
  if (!S.run) S.view = "intake";
  if (S.run) {
    const firstCand = S.run.discovery.entries.find(e => ["direct", "transferable", "insufficient"].includes(e.group));
    if (!S.run.discovery.entries.some(e => e.candidate_id === S.selCandidate)) S.selCandidate = firstCand ? firstCand.candidate_id : null;
    if (!S.run.result.findings.some(f => f.id === S.selFinding)) S.selFinding = S.run.result.findings.length ? S.run.result.findings[0].id : null;
  }
}

$("reviewer").value = (() => { try { return localStorage.getItem("sa-reviewer") || ""; } catch (e) { return ""; } })();
$("reviewer").addEventListener("input", () => { try { localStorage.setItem("sa-reviewer", reviewer()); } catch (e) { /* storage unavailable */ } });
guarded(refreshState);
