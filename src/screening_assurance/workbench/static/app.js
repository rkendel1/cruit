/* Screening Assurance recruiter workbench — thin presentation layer.
 * All matching, grouping, evidence interpretation, simulation and validation happen in the Python engine.
 * This file only fetches results, renders them with textContent (never innerHTML of data),
 * and posts explicit, attributed decisions back to the local server. */
"use strict";

const TOKEN = document.querySelector('meta[name="sa-token"]').content;
const S = { state: null, session: null, run: null, view: "home", selCandidate: null, selFinding: null,
            levelFilter: "all", validation: null, files: {}, evalOut: null, verify: {}, valSample: null,
            tour: { active: false, step: 0 }, reviewer: "" };

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
function add(el, ...kids) { el.append(...kids.flat(Infinity).filter(k => k !== null && k !== undefined && k !== false)); return el; }
const short = (s, n = 12) => (s ? String(s).slice(0, n) : "");
const when = (iso) => (iso || "").slice(0, 16).replace("T", " ");
const plural = (n, one, many) => n + " " + (n === 1 ? one : (many || one + "s"));
function toast(msg, err) {
  const t = $("toast"); t.textContent = msg; t.className = "toast" + (err ? " err" : ""); t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => { t.hidden = true; }, err ? 7000 : 3500);
}
function announce(msg) { $("announce").textContent = ""; setTimeout(() => { $("announce").textContent = msg; }, 30); }
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

// ------------------------------------------------------------------ attribution (one name, asked for where it is used)
function reviewer() { return (S.reviewer || "").trim(); }
function setReviewer(v) { S.reviewer = v; try { localStorage.setItem("sa-reviewer", v); } catch (e) { /* storage unavailable */ } }
function nameField(label) {
  return h("label", { class: "field" }, label || "Your name (decisions are attributed to you)",
    h("input", { type: "text", class: "name-input", value: S.reviewer, autocomplete: "name", placeholder: "e.g. Lee Morgan",
      oninput: (ev) => { setReviewer(ev.target.value); document.querySelectorAll(".name-input").forEach(x => { if (x !== ev.target) x.value = ev.target.value; }); } }));
}
function needReviewer(scope) {
  if (reviewer()) return true;
  toast("Add your name first. Every decision and run is attributed to the person who made it.", true);
  const f = (scope || document).querySelector(".name-input") || document.querySelector(".name-input");
  if (f) f.focus();
  return false;
}
const isDemo = () => !!(S.session && S.session.mode === "demo");
const runActor = () => reviewer() || (isDemo() ? "demo visitor" : "");

// ------------------------------------------------------------------ vocabulary (plain language first)
const GROUPS = {
  direct: ["Direct evidence", "Their record shows every required requirement directly."],
  transferable: ["Transferable evidence — verify", "Every required requirement is covered, at least one through related experience you need to confirm."],
  insufficient: ["Insufficient evidence — needs more information", "Some required evidence is there, but the record is partial or a mandatory requirement can't be checked yet."],
  not_surfaced: ["Not surfaced", "A mandatory requirement is not met, or required evidence is missing from a complete record."],
  blocked: ["Not available for action", "Not authorized for this use, authorization expired, or evidence too old. Their evidence is not shown."],
  active_workflow: ["Already in active review", "Already moving in your ATS, so they are not repeated here."],
};
const SURFACED = ["direct", "transferable", "insufficient"];
const STATUS = {
  evidenced: ["Supported by their record", "ok", "observed"], alternative_path: ["Supported through related experience", "warn", "verify"],
  insufficient: ["Below the stated threshold", "warn", "verify"], not_evidenced: ["Not in their record", "muted", null],
  pending_clarification: ["Requirement's necessity not confirmed", "warn", "verify"], protected_missing: ["Mandatory credential missing", "bad", "protected"],
};
const KINDS = {
  observed: ["Observed", "Directly supported by the supplied records or evidence."],
  simulated: ["Simulated", "The result of applying a proposed correction to the supplied inputs. Nothing was changed."],
  verify: ["Needs verification", "Cannot be established from the available evidence; a person has to check it."],
  protected: ["Protected requirement", "A mandatory condition that no proposed correction can bypass."],
};
function kindTag(k) { return h("span", { class: "kind k-" + k, title: KINDS[k][1] }, KINDS[k][0]); }
function legend() {
  return h("details", { class: "legend" }, h("summary", {}, "What the labels mean"),
    h("dl", { class: "kv" }, Object.keys(KINDS).map(k => [h("dt", {}, kindTag(k)), h("dd", {}, KINDS[k][1])])));
}
const CAND_DISP = { review_in_ats: "Review in the ATS", request_more_information: "Request more information",
                    not_a_fit_for_this_role: "Not a fit for this role", defer: "Defer" };
const FIND_DISP = { accepted: "Accept the concern", rejected: "Reject the concern", deferred: "Defer", requested_evidence: "Request more evidence",
                    confirmed_necessary: "Confirm the requirement is necessary", reclassified_preferred: "Reclassify as preferred",
                    approved_candidate_review: "Approve candidate review" };
const LEVEL = { 1: "Level 1 — demonstrable inconsistency", 2: "Level 2 — missed-talent risk", 3: "Level 3 — measured impact" };
const CONFIG = { ats_export_verified: ["From a supplied ATS configuration export — not a live ATS audit", "ok"],
                 ats_api_verified: ["Read from the ATS at export time — not a live audit", "ok"],
                 recruiter_documentation: ["From recruiter documentation — not verified against the ATS", "warn"],
                 not_supplied: ["No screening rules supplied", "bad"] };
const cfgLabel = (k) => (CONFIG[k] || ["Unknown source", "muted"])[0];
function riskLabel(k) { return (S.state.risk_categories || {})[k] || k; }
function scopeOf(f) {
  if (f.candidate_id) return ["Candidate-specific", "One person's result under the supplied rules."];
  if (f.rule_id || f.requirement_id) return ["Rule-level", "A risk in a supplied rule or requirement, whoever it affects."];
  return ["Whole requisition", "A pattern across this requisition's results."];
}
function scopeTag(f) { const s = scopeOf(f); return h("span", { class: "tag outline", title: s[1] }, s[0]); }
function entry(cid) { return S.run && S.run.discovery.entries.find(x => x.candidate_id === cid); }
function isPool(cid) { const e = entry(cid); return !!(e && e.source.kind === "candidate_pool"); }

// ------------------------------------------------------------------ shell
const VIEWS = [["overview", "Overview"], ["role", "The role"], ["candidates", "Candidates"], ["rules", "Screening rules"], ["decisions", "Decisions & export"]];
function renderShell() {
  const prov = $("provenance"); prov.replaceChildren();
  if (S.session) prov.append(h("span", { class: "req-name" }, S.session.title, h("span", { class: "sub" }, " " + S.session.requisition_id)));
  if (S.run) prov.append(h("details", { class: "techpop" }, h("summary", {}, "Run details"),
    h("dl", { class: "kv" }, h("dt", {}, "Run"), h("dd", { class: "mono" }, S.run.run.run_id), h("dt", {}, "Run by"), h("dd", {}, S.run.run.run_by + ", " + when(S.run.run.run_at)),
      h("dt", {}, "Knowledge"), h("dd", { class: "mono" }, S.run.run.knowledge.fingerprint), h("dt", {}, "Engine"), h("dd", {}, S.run.run.engine_version),
      h("dt", {}, "Inputs"), h("dd", { class: "mono" }, Object.entries(S.run.run.inputs).map(([k, v]) => h("div", {}, k + " " + short(v, 10)))))));

  const band = $("modeband"); band.replaceChildren(); band.hidden = true;
  if (isDemo()) {
    band.hidden = false; band.className = "modeband demo";
    add(band, h("b", {}, "Demo"), h("span", {}, "Fictional Northwind sample data. Kept separate from your own sessions; no real candidate is involved."),
      h("span", { class: "grow" }),
      !S.tour.active && S.run ? h("button", { class: "btn small", onclick: () => startTour(S.tour.step || 0) }, S.tour.step ? "Resume guided tour" : "Start guided tour") : null,
      h("button", { class: "btn small", onclick: goHome }, "Leave demo"));
  } else if (S.session) {
    band.hidden = false; band.className = "modeband real";
    band.append(h("b", {}, "Your requisition"), h("span", {}, "Your authorized inputs, stored only on this computer."),
      h("span", { class: "grow" }), h("button", { class: "btn small", onclick: goHome }, "All sessions"));
  }

  const nav = $("steps"); nav.replaceChildren();
  if (S.tour.active && S.session) return renderTourNav(nav);
  if (!S.session) {
    nav.append(navBtn("home", "Start"), navBtn("upload", "Review my requisition"));
    nav.append(h("p", { class: "hint" }, "Nothing here contacts, advances or rejects anyone. Results are for human review."));
    return;
  }
  VIEWS.forEach(([id, label]) => nav.append(navBtn(id, label, id !== "role" && !S.run)));
  nav.append(h("p", { class: "hint" }, S.run ? "Move between views in any order. Nothing here contacts, advances or rejects anyone." : "Analyse the requisition to see candidates and screening rules."));
}
function navBtn(id, label, disabled) {
  return h("button", { "aria-current": S.view === id ? "page" : false, disabled: !!disabled, onclick: () => { S.view = id; render(true); } }, label);
}
function render(focus) {
  renderShell();
  const m = $("main"); m.replaceChildren();
  if (S.tour.active && S.session && S.run) m.append(viewTour());
  else {
    const views = { home: viewHome, upload: viewUpload, overview: viewOverview, role: viewRole, candidates: viewCandidates, rules: viewRules, decisions: viewDecisions };
    m.append((views[S.view] || viewHome)());
  }
  if (focus) { const hd = m.querySelector("h1, h2"); if (hd) { hd.setAttribute("tabindex", "-1"); hd.focus({ preventScroll: false }); } window.scrollTo(0, 0); }
}
function goHome() { S.session = null; S.run = null; S.tour.active = false; S.view = "home"; guarded(refreshState); }

// ------------------------------------------------------------------ home: one obvious starting point
function viewHome() {
  const st = S.state;
  const real = st.sessions.filter(x => x.mode !== "demo"), demo = st.sessions.filter(x => x.mode === "demo");
  const choice = h("select", { "aria-label": "Sample requisition" }, st.demo_examples.map(e => h("option", { value: e.id }, e.title + " (" + e.id + ")")));
  choice.value = st.default_demo;
  const startBtn = h("button", { class: "btn primary big", onclick: () => guarded(async () => {
    startBtn.disabled = true; startBtn.textContent = "Preparing the sample…";
    try {
      const out = await api("POST", "demo", { example: choice.value, actor: reviewer() });
      await openSession(out.session_id, out.run_id);
      S.tour = { active: true, step: 0 }; render(true);
      announce("Demo ready. Step: what might we be missing for this role?");
    } finally { startBtn.disabled = false; startBtn.textContent = "Start the guided demo"; }
  }) }, "Start the guided demo");
  const root = h("div", { class: "home" });
  root.append(h("section", { class: "hero" },
    h("h1", {}, "Find candidates your process may be missing."),
    h("p", { class: "lede" }, "Understand why. Decide what to do — with evidence."),
    h("p", { class: "sub" }, "Screening Assurance reads a requisition's actual requirements and its screening rules, then looks at the candidate evidence you are allowed to use. It shows who deserves a second look, which rules may be keeping them out, and what a correction would change. People make every decision.")));
  root.append(h("div", { class: "paths" },
    h("section", { class: "panel path demo" },
      h("h2", {}, "Try the guided demo"),
      h("p", {}, "Open a ready-to-run sample requisition with fictional, de-identified candidates and walk through a real result in six short steps."),
      h("ul", { class: "plain small" }, h("li", {}, "No ATS connection, account or setup"), h("li", {}, "No personal candidate data"), h("li", {}, "Kept separate from your own work")),
      h("label", { class: "field mt10" }, "Sample requisition", choice),
      h("div", { class: "row mt12" }, startBtn)),
    h("section", { class: "panel path" },
      h("h2", {}, "Review my requisition"),
      h("p", {}, "Use your own authorized, de-identified inputs: a requisition with its screening rules, your employer policy, and optionally current applicants and a talent pool."),
      h("ul", { class: "plain small" }, h("li", {}, "Files stay on this computer"), h("li", {}, "Names, contact details and protected characteristics are rejected"), h("li", {}, "Never mixed with sample data")),
      h("div", { class: "row mt12" }, h("button", { class: "btn big", onclick: () => { S.view = "upload"; render(true); } }, "Review my requisition")))));
  if (real.length) root.append(sessionsPanel("Your sessions", real, "Open"));
  if (demo.length) root.append(h("details", { class: "panel mt14" }, h("summary", {}, "Previous demo sessions (" + demo.length + ")"), sessionsTable(demo, "Open")));
  return root;
}
function sessionsPanel(title, rows, verb) { return h("section", { class: "panel mt14" }, h("h3", {}, title), sessionsTable(rows, verb)); }
function sessionsTable(rows, verb) {
  return h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Requisition"), h("th", {}, "Created"), h("th", {}, "Candidate data kept until"), h("th", {}, ""))),
    h("tbody", {}, rows.slice().reverse().map(x => h("tr", {}, h("td", {}, h("b", {}, x.title), h("div", { class: "sub" }, x.requisition_id + (x.runs ? "" : " · not analysed yet"))),
      h("td", {}, when(x.created_at)),
      h("td", {}, x.candidate_data_deleted ? "Deleted (retention)" : x.retention.delete_after ? x.retention.delete_after.slice(0, 10) : "No candidate data"),
      h("td", {}, h("div", { class: "row" }, h("button", { class: "btn", onclick: () => guarded(async () => { await openSession(x.id); S.tour.active = false; S.view = S.run ? "overview" : "role"; render(true); }) }, verb),
        h("button", { class: "btn danger", "aria-label": "Delete session " + x.id, onclick: () => guarded(async () => {
          if (!confirm("Delete this session and all its candidate data from this computer? This cannot be undone.")) return;
          await api("DELETE", "sessions/" + x.id, { actor: reviewer() || (x.mode === "demo" ? "demo visitor" : "workbench user"), reason: "deleted by reviewer" });
          await refreshState(); toast("Session deleted.");
        }) }, "Delete"))))))));
}

// ------------------------------------------------------------------ real path: upload, validate, analyse
const KIND_HELP = {
  requisition: ["Requisition and screening rules", "The job's requirements and the knockout questions or filters your ATS applies. Required."],
  policy: ["Employer policy", "What your organization treats as non-negotiable and which equivalent experience it accepts. Required."],
  candidates: ["Current applicants", "De-identified applicant evidence for this requisition. Needed to find candidates."],
  candidate_pool: ["Authorized talent pool", "Prior applicants or community records you may use for other roles. Optional."],
  outcomes: ["Observed outcomes", "Before/after measurements, if you have them. Optional; shown apart from estimates."],
};
function kindLabel(k) { return (KIND_HELP[k] || [k])[0]; }
function viewUpload() {
  const st = S.state;
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Review my requisition"),
    h("p", {}, "Add your files. Each one is checked as soon as you choose it; nothing leaves this computer."))));
  const rows = Object.entries(st.input_kinds).map(([kind, info]) => {
    const input = h("input", { type: "file", accept: ".yaml,.yml,.json", "aria-label": kindLabel(kind), onchange: (ev) => readFile(kind, ev.target.files[0]) });
    const res = S.validation && S.validation.report.find(r => r.kind === kind);
    return h("div", { class: "filerow" },
      h("div", {}, h("b", {}, kindLabel(kind)), h("div", { class: "sub" }, KIND_HELP[kind][1])),
      h("div", {}, input, S.files[kind] ? h("div", { class: "sub" }, S.files[kind].name) : null),
      h("div", { class: "status" }, res ? statusTag(res) : (info.required ? h("span", { class: "tag outline" }, "Required") : h("span", { class: "tag muted" }, "Optional")),
        res && res.errors.length ? h("ul", { class: "plain small" }, res.errors.map(x => h("li", {}, x))) : null,
        res && res.notes ? h("ul", { class: "plain small" }, res.notes.map(x => h("li", {}, x))) : null));
  });
  const v = S.validation;
  const missing = v ? v.report.filter(r => r.status === "missing").map(r => kindLabel(r.kind)) : [];
  const invalid = v ? v.report.filter(r => r.status === "invalid").map(r => kindLabel(r.kind)) : [];
  const noCands = v && v.ok && !S.files.candidates && !S.files.candidate_pool;
  let next = "Choose the requisition and employer policy files to begin.";
  if (v && invalid.length) next = "Fix " + invalid.join(" and ") + " (details beside each file), then choose the corrected file.";
  else if (v && missing.length) next = "Add " + missing.join(" and ") + " to continue.";
  else if (v && v.ok) next = "Ready. Screening rules: " + v.summary.screening_configuration_label + "." + (noCands ? " No candidate evidence was added, so only the screening rules can be checked." : "");
  const sel = knowledgeSelect();
  const go = h("button", { class: "btn primary big", disabled: !(v && v.ok), onclick: () => guarded(async () => {
    if (!needReviewer(root)) return;
    go.disabled = true; go.textContent = "Analysing…";
    try {
      const meta = await api("POST", "sessions", { files: fileTexts(), actor: reviewer() });
      const run = await api("POST", "sessions/" + meta.id + "/runs", { knowledge: sel.value, actor: reviewer() });
      S.files = {}; S.validation = null; await openSession(meta.id, run.run_id); S.view = "overview"; render(true);
    } finally { go.disabled = !(S.validation && S.validation.ok); go.textContent = "Analyse"; }
  }) }, "Analyse");
  root.append(h("section", { class: "panel" }, h("div", { class: "files" }, rows),
    h("div", { class: "banner mt12 " + (v && v.ok ? "info" : v ? "bad" : "neutral"), role: "status" }, next),
    h("div", { class: "row mt12 align-end" }, h("div", { class: "w280" }, nameField("Your name (runs and decisions are attributed to you)")), go),
    h("details", { class: "mt12" }, h("summary", {}, "Advanced: knowledge version"), h("label", { class: "field mt8" }, "Knowledge used for the analysis", sel),
      h("p", { class: "sub mt8" }, "Defaults to the approved production knowledge. The exact documents used are copied into each run so results can be reproduced."))));
  const real = st.sessions.filter(x => x.mode !== "demo");
  root.append(real.length ? sessionsPanel("Your sessions", real, "Open") : h("p", { class: "sub" }, "You have no sessions yet. Your analysed requisitions will appear here."));
  return root;
}
function knowledgeSelect() {
  const sel = h("select", {}, S.state.knowledge.map(k => h("option", { value: k.spec, disabled: !k.fingerprint }, k.label + (k.fingerprint ? " — " + k.fingerprint : ""))));
  const prod = S.state.knowledge.find(k => k.spec === "env:production" && k.fingerprint);
  sel.value = prod ? prod.spec : (S.state.knowledge.find(k => k.fingerprint) || {}).spec;
  return sel;
}
function statusTag(r) {
  const m = { valid: ["Checked", "ok"], invalid: ["Needs fixing", "bad"], missing: ["Missing", "bad"], not_supplied: ["Not added", "muted"] }[r.status];
  return h("span", { class: "tag " + m[1] }, m[0]);
}
function readFile(kind, file) {
  if (!file) { delete S.files[kind]; return; }
  if (file.size > S.state.max_file_bytes) { toast(file.name + " is larger than the " + (S.state.max_file_bytes / 1048576) + " MB limit.", true); return; }
  const fr = new FileReader();
  fr.onload = () => guarded(async () => {
    S.files[kind] = { name: file.name, text: String(fr.result) };
    S.validation = await api("POST", "validate", { files: fileTexts() }); render();
  });
  fr.readAsText(file);
}
function fileTexts() { const o = {}; for (const [k, v] of Object.entries(S.files)) o[k] = v.text; return o; }

// ------------------------------------------------------------------ overview: what might we be missing?
function viewOverview(inTour) {
  const g = S.run.guide.summary, c = g.counts;
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" },
    h("h2", {}, "What might we be missing for this role?"),
    h("p", {}, S.session.title + ". Two views of the same requisition: candidates whose evidence deserves a human look, and the screening rules that may be keeping people like them out."))));
  const noCands = g.candidates_considered === 0;
  const candCard = h("section", { class: "panel value" }, h("p", { class: "eyebrow" }, "Find relevant candidates"),
    noCands ? [h("h3", {}, "No candidate evidence was supplied"), h("p", {}, "Add current applicants or an authorized talent pool to see who deserves review. The screening rules can still be checked on the right.")] : [
      h("h3", { class: "big" }, plural(g.surfaced, "candidate") + " have evidence worth a human review"),
      h("p", {}, (g.excluded_applicants_with_evidence.length ? plural(g.excluded_applicants_with_evidence.length, "of them was", "of them were") + " rejected by the current process. " : "") +
        (g.surfaced_from_pool ? g.surfaced_from_pool + " come from the authorized talent pool. " : "") +
        "Evidence is matched to the actual requirements, including relevant experience described in different words."),
      h("ul", { class: "groups" }, ["direct", "transferable", "insufficient", "not_surfaced", "blocked", "active_workflow"].filter(k => c[k] || SURFACED.includes(k)).map(k =>
        h("li", {}, h("b", { class: "n" }, c[k]), h("div", {}, h("span", { class: "gname g-" + k }, GROUPS[k][0]), h("span", { class: "sub" }, GROUPS[k][1]))))),
      !inTour ? h("div", { class: "row mt12" }, h("button", { class: "btn primary", onclick: () => { S.view = "candidates"; render(true); } }, "See candidates")) : null]);
  const ruleCard = h("section", { class: "panel value" }, h("p", { class: "eyebrow" }, "Identify restrictive screening rules"),
    g.rule_risks ? [
      h("h3", { class: "big" }, plural(g.rule_risks, "screening-rule risk") + " found"),
      h("p", {}, g.corrections_simulated ? plural(g.corrections_simulated, "proposed correction") + " can be simulated against the same candidates. " +
        (g.newly_eligible_any_correction.length ? "Together they would make " + plural(g.newly_eligible_any_correction.length, "rejected applicant") + " eligible for human review — not qualified, just reviewed." : "") : "None of the risks can be simulated against candidate evidence; they are rule-level concerns."),
      g.top_rule_risks.length ? h("ol", { class: "risks" }, g.top_rule_risks.map(t => h("li", {},
        h("a", { href: "#", onclick: (ev) => { ev.preventDefault(); S.selFinding = t.finding_id; S.tour.active = false; S.view = "rules"; render(true); } }, t.title),
        h("span", { class: "sub" }, " · " + riskLabel(t.risk_category) + " · " + (t.newly_eligible.length ? plural(t.newly_eligible.length, "more person", "more people") + " eligible for review (simulated)" : "no one newly eligible"))))) : null,
      !inTour ? h("div", { class: "row mt12" }, h("button", { class: "btn primary", onclick: () => { S.view = "rules"; render(true); } }, "See screening rules")) : null]
      : [h("h3", {}, "No screening-rule risks found"), h("p", {}, g.screening_configuration === "not_supplied" ? "No screening rules were supplied, so there was nothing to check. Add the ATS configuration export to the requisition file." : "The supplied rules are consistent with the posted requirements.")]);
  root.append(h("div", { class: "grid2" }, candCard, ruleCard));
  const notes = [];
  if (g.protected_requirements.length) notes.push(h("li", {}, kindTag("protected"), " Mandatory rule " + g.protected_requirements.join(", ") + " is protected: no correction can bypass it."));
  if (g.unexplained_exclusions.length) notes.push(h("li", {}, kindTag("verify"), " " + plural(g.unexplained_exclusions.length, "rejection") + " (" + g.unexplained_exclusions.join(", ") + ") can't be explained by the supplied rules. They are not counted as missed candidates."));
  if (g.needs_verification.length) notes.push(h("li", {}, kindTag("verify"), " " + plural(g.needs_verification.length, "surfaced candidate") + " rely on related experience or partial records you need to confirm."));
  notes.push(h("li", {}, kindTag("observed"), " Screening rules: " + cfgLabel(g.screening_configuration) + "."));
  root.append(h("section", { class: "panel" }, h("h3", {}, "What to keep in mind"), h("ul", { class: "plain notes" }, notes),
    h("p", { class: "sub mt8" }, "No ranking, scores or match percentages: groups describe what the evidence supports. Nothing here qualifies, rejects or contacts anyone.")));
  return root;
}

// ------------------------------------------------------------------ the role
function viewRole(inTour) {
  const s = S.session;
  const root = h("div", { class: "stack" });
  if (!inTour) root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "The role: " + s.title),
    h("p", {}, "What the analysis uses: the posted requirements, the screening rules your process applies, your employer policy and the candidate evidence you supplied."))));
  if (s.candidate_data_deleted) root.append(h("div", { class: "banner bad" }, "Candidate data for this session was deleted when its retention period ended. Start a new session to analyse candidates again."));
  if (!inTour && !S.run && !s.candidate_data_deleted) root.append(analysePanel(s));
  const sum = s.summary;
  root.append(h("section", { class: "panel" }, h("h3", {}, "Requirements"),
    h("ul", { class: "reqs" }, s.requisition.requirements.map(r => {
      const prot = protectedReq(r.id);
      return h("li", {}, h("b", { class: "rid" }, r.id), h("div", {}, h("div", {}, r.text),
        h("div", { class: "tags mt6" }, h("span", { class: "tag " + (r.stated_as === "required" ? "accent" : "muted") }, r.stated_as === "required" ? "Required" : "Preferred"),
          r.accepts_equivalent ? h("span", { class: "tag outline" }, "Equivalent experience accepted") : null, prot ? kindTag("protected") : null)));
    }))));
  root.append(h("section", { class: "panel" }, h("h3", {}, "Screening rules your process applies"),
    h("p", { class: "sub" }, cfgLabel(sum.screening_configuration) + ". These are exactly what the analysis checks; it is not connected to your ATS."),
    s.requisition.screening_rules.length ? h("ul", { class: "reqs" }, s.requisition.screening_rules.map(r => h("li", {}, h("b", { class: "rid" }, r.id),
      h("div", {}, h("div", {}, r.text), h("div", { class: "sub" }, (r.action === "reject" ? "Rejects automatically" : r.action.replace(/_/g, " ")) + " · " +
        (r.linked_requirement ? "checks requirement " + r.linked_requirement : "not linked to a posted requirement")))))) : h("p", {}, "No screening rules supplied.")));
  root.append(h("div", { class: "grid2" },
    h("section", { class: "panel" }, h("h3", {}, "Candidate evidence used"),
      h("dl", { class: "kv" },
        h("dt", {}, "Applicants"), h("dd", {}, sum.current_applicants === null ? "None supplied" : sum.current_applicants + " de-identified record(s)"),
        h("dt", {}, "Talent pool"), h("dd", {}, sum.pool ? sum.pool.records + " record(s) authorized for " + sum.pool.permitted_uses.join(", ").replace(/_/g, " ") + "; evidence older than " + sum.pool.max_evidence_age_days + " days is not used" : "None supplied"),
        h("dt", {}, "Never used"), h("dd", {}, "Names, contact details, photos and protected characteristics are rejected on import."),
        h("dt", {}, "Kept until"), h("dd", {}, s.retention.delete_after ? s.retention.delete_after.slice(0, 10) + ", then deleted from this computer" : "No candidate data in this session"))),
    h("section", { class: "panel" }, h("h3", {}, "Employer policy"),
      h("h4", {}, "Non-negotiable"), listOrNone(s.policy.non_negotiable.map(n => n.concept + " — " + n.rationale)),
      h("h4", { class: "mt10" }, "Equivalent experience accepted"), listOrNone(s.policy.accepted_equivalencies.map(a => a.id.replace(/^eq\./, "").replace(/[.-]/g, " ") + (a.rationale ? " — " + a.rationale : ""))),
      h("h4", { class: "mt10" }, "Equivalent experience not accepted"), listOrNone(s.policy.rejected_equivalencies.map(a => a.id.replace(/^eq\./, "").replace(/[.-]/g, " ") + " — " + a.rationale)))));
  if (!inTour) root.append(h("details", { class: "panel" }, h("summary", {}, "Technical details: input files and fingerprints"),
    h("div", { class: "tbl mt8" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Input"), h("th", {}, "Status"), h("th", {}, "sha256"), h("th", {}, "Size"))),
      h("tbody", {}, Object.keys(S.state.input_kinds).map(k => { const got = s.inputs[k];
        return h("tr", {}, h("td", {}, kindLabel(k)), h("td", {}, got ? "Supplied" : "Not supplied"), h("td", { class: "mono" }, got ? short(got.sha256, 16) : ""), h("td", {}, got ? (got.bytes / 1024).toFixed(1) + " KB" : "")); })))),
    S.run ? analysePanel(s) : null));
  return root;
}
function protectedReq(rid) { return S.run && (S.run.result.requirements || []).some(r => r.id === rid && r.protected); }
function listOrNone(items) { return items.length ? h("ul", { class: "plain small" }, items.map(i => h("li", {}, i))) : h("p", { class: "sub" }, "None"); }
function analysePanel(s) {
  const sel = knowledgeSelect();
  const btn = h("button", { class: "btn primary", disabled: !!s.candidate_data_deleted, onclick: () => guarded(async () => {
    if (!runActor()) return needReviewer();
    btn.disabled = true; btn.textContent = "Analysing…";
    try {
      const run = await api("POST", "sessions/" + s.id + "/runs", { knowledge: sel.value, actor: runActor() });
      await openSession(s.id, run.run_id); S.view = "overview"; render(true);
      const co = run.carried_over, n = co.finding_decisions_applied.length + co.candidate_decisions_applied.length;
      toast("Analysis complete." + (n ? " " + n + " earlier decision(s) carried over." : ""));
    } finally { btn.disabled = false; btn.textContent = S.run ? "Analyse again" : "Analyse"; }
  }) }, S.run ? "Analyse again" : "Analyse");
  return h("section", { class: "panel mt12" }, h("h3", {}, S.run ? "Analyse again" : "Analyse this requisition"),
    isDemo() ? null : nameField(),
    h("details", { class: "mt8" }, h("summary", {}, "Advanced: knowledge version"), h("label", { class: "field mt8" }, "Knowledge", sel)),
    h("div", { class: "row mt10" }, btn),
    s.runs.length ? h("details", { class: "mt12" }, h("summary", {}, "Earlier runs (" + s.runs.length + ")"), h("ul", { class: "plain small" },
      s.runs.slice().reverse().map(r => h("li", {}, h("a", { href: "#", onclick: (e) => { e.preventDefault(); guarded(async () => { await openSession(s.id, r.run_id); S.view = "overview"; render(true); }); } }, when(r.run_at)),
        " by " + r.run_by + ", knowledge " + r.knowledge.fingerprint)))) : null);
}

// ------------------------------------------------------------------ candidates
function candDecision(id) { return (S.session.review_decisions || []).find(d => d.candidate_id === id); }
function viewCandidates() {
  const d = S.run.discovery, c = d.counts;
  const root = h("div", {});
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Candidates"),
    h("p", {}, "Grouped by what their evidence supports for this role's requirements. There is no ranking or score, and appearing here does not mean a person is qualified."))));
  const surfaced = d.entries.filter(e => SURFACED.includes(e.group));
  if (!d.entries.length) {
    root.append(h("div", { class: "panel empty-state" }, h("h3", {}, "No candidate evidence in this session"),
      h("p", {}, "Add current applicants or an authorized talent pool to find candidates. You can still review the screening rules."),
      h("div", { class: "row mt10" }, h("button", { class: "btn", onclick: () => { S.view = "rules"; render(true); } }, "Review screening rules"),
        h("button", { class: "btn", onclick: () => { S.view = "upload"; S.session = null; S.run = null; render(true); } }, "Start a session with candidates"))));
    return root;
  }
  const list = h("div", { class: "list", "aria-label": "Candidates to review" });
  if (!surfaced.length) list.append(h("p", { class: "group-head" }, "No one's supplied evidence supports review for this role. See below for why records were not surfaced."));
  for (const g of SURFACED) {
    const items = d.entries.filter(e => e.group === g);
    if (!items.length) continue;
    list.append(h("div", { class: "group-head" }, h("h4", {}, GROUPS[g][0], h("span", { class: "sub" }, items.length)), h("p", {}, GROUPS[g][1])));
    items.forEach(e => list.append(candidateItem(e)));
  }
  root.append(h("div", { class: "split mt14" }, list, h("div", { class: "detail" }, candidateDetail(S.selCandidate, { decision: true }))));
  const listed = d.entries.filter(e => (e.group === "not_surfaced" || e.group === "blocked") && e.listable);
  const unlisted = d.entries.filter(e => e.group === "not_surfaced" && !e.listable).length;
  root.append(h("details", { class: "panel mt18" }, h("summary", {}, "Not surfaced or not available (" + (listed.length + unlisted + c.active_workflow) + ")"),
    h("p", { class: "sub mt8" }, "Only reasons the supplied data can explain are listed. " + plural(unlisted, "record") + " with no evidence for any required requirement are counted, not listed. " + c.active_workflow + " already in active review."),
    listed.length ? h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Candidate"), h("th", {}, "Group"), h("th", {}, "Reason"))),
      h("tbody", {}, listed.map(e => h("tr", {}, h("td", {}, h("b", {}, e.candidate_id), h("div", { class: "sub" }, e.source.kind === "candidate_pool" ? "Talent pool" : "Applicant")),
        h("td", {}, h("span", { class: "tag " + (e.group === "blocked" ? "muted" : "outline") }, GROUPS[e.group][0])), h("td", {}, e.reason)))))) : null));
  return root;
}
function reqTags(e) {
  return e.requirements.filter(r => r.stated_as === "required").map(r => {
    const st = STATUS[r.status] || [r.status, "muted"];
    const issue = e.mandatory_issues.find(m => m.requirement === r.id);
    const cls = issue && issue.issue === "cannot_verify" ? "warn" : st[1];
    return h("span", { class: "tag " + cls, title: r.text + " — " + (issue && issue.issue === "cannot_verify" ? "cannot verify" : st[0]) }, r.id + (cls === "ok" ? " ✓" : cls === "warn" ? " ?" : " ✕"));
  });
}
function candidateItem(e) {
  const dec = candDecision(e.candidate_id);
  return h("button", { class: "item", "aria-pressed": S.selCandidate === e.candidate_id ? "true" : "false",
    onclick: () => { S.selCandidate = e.candidate_id; render(); } },
    h("div", { class: "line1" }, h("span", { class: "id" }, e.candidate_id), h("span", { class: "src" }, e.source.kind === "candidate_pool" ? "Talent pool" : (e.screening.excluded_by && e.screening.excluded_by.length ? "Applicant · rejected by rules" : "Applicant"))),
    h("div", { class: "tags" }, reqTags(e), dec ? h("span", { class: "tag accent" }, CAND_DISP[dec.disposition]) : null));
}
function rulesKeepingOut(cid) {
  return S.run.result.findings.filter(f => f.risk_category && !f.candidate_id && ((f.simulation || {}).categories || {}).newly_eligible_for_review && f.simulation.categories.newly_eligible_for_review.includes(cid));
}
function candidateDetail(cid, opts) {
  const e = entry(cid);
  if (!e || !SURFACED.includes(e.group)) return h("div", { class: "panel empty" }, "Select a candidate to see why they appeared, the evidence, and what remains unknown.");
  const p = h("div", { class: "panel detail-body" });
  p.append(h("div", { class: "detail-head" }, h("div", {}, h("h2", {}, e.candidate_id),
    h("div", { class: "sub" }, e.source.kind === "candidate_pool" ? "Talent-pool record (did not apply to this role)" : "Applied to this role")),
    h("span", { class: "tag " + (e.group === "direct" ? "ok" : "warn") }, GROUPS[e.group][0])));
  p.append(h("div", { class: "section" }, h("h4", {}, "Why this person is worth reviewing"), h("ul", { class: "plain" }, e.why.map(w => h("li", {}, w)))));
  p.append(h("div", { class: "section" }, h("h4", {}, "Evidence for each requirement"), ledger(e.requirements, e)));
  const unknown = e.mandatory_issues.map(m => h("li", {}, m.issue === "not_satisfied" ? kindTag("protected") : kindTag("verify"), " ", h("b", {}, m.requirement + ": "), m.detail))
    .concat(e.unverified.map(u => h("li", {}, kindTag("verify"), " ", h("b", {}, u.requirement + ": "), u.reason)));
  p.append(h("div", { class: "section" }, h("h4", {}, "What remains unknown"),
    h("ul", { class: "plain" }, unknown, h("li", {}, "Whether this person is qualified. That is for a recruiter to decide after review."))));
  if (e.verify_next.length) p.append(h("div", { class: "section" }, h("h4", {}, "What to verify next"), h("ul", { class: "plain" }, e.verify_next.map(v => h("li", {}, v)))));
  const sc = e.screening, keep = rulesKeepingOut(e.candidate_id);
  p.append(h("div", { class: "section" }, h("h4", {}, "Screening rules and this person"),
    sc.applied_to_requisition ? h("div", {},
      sc.excluded_by.length ? h("ul", { class: "plain" }, sc.excluded_by.map(x => h("li", {}, kindTag("observed"), " Rejected by ", h("b", {}, x.rule), " — " + x.reason))) : h("p", {}, kindTag("verify"), " " + (sc.note || "Not excluded by any supplied rule.")),
      h("p", { class: "sub" }, "Exclusion " + sc.basis + (sc.established ? "." : "; treat as indicative.")))
    : h("p", {}, sc.basis),
    keep.length ? h("div", { class: "mt8" }, h("p", { class: "small" }, kindTag("simulated"), " Proposed corrections that would make this person eligible for review:"),
      h("ul", { class: "plain small" }, keep.map(f => h("li", {}, findingLink(f.id, f.title))))) : null));
  p.append(h("details", { class: "section tech" }, h("summary", {}, "Record details and provenance"), h("dl", { class: "kv mt8" },
    h("dt", {}, "Source record"), h("dd", { class: "mono" }, e.source.system + " / " + e.source.record_ref),
    h("dt", {}, "Evidence source"), h("dd", {}, (e.source.evidence_provenance || "").replace(/_/g, " ")),
    h("dt", {}, "Evidence updated"), h("dd", {}, e.freshness.evidence_updated_at ? e.freshness.evidence_updated_at + " (" + e.freshness.age_days + " days before assessment, limit " + e.freshness.max_age_days + ")" : e.freshness.note || "—"),
    e.prior_applications.length ? [h("dt", {}, "Prior applications"), h("dd", {}, h("ul", { class: "plain" }, e.prior_applications.map(a => h("li", {}, a.requisition_ref + (a.role_title ? " " + a.role_title : "") + ", " + a.applied_at + ", " + a.outcome.replace(/_/g, " ") + (a.recorded_reason ? " (" + a.recorded_reason + ")" : "")))))] : null,
    h("dt", {}, "Constraints"), h("dd", {}, h("ul", { class: "plain" }, e.constraints.map(x => h("li", {}, x)))),
    h("dt", {}, "Run"), h("dd", { class: "mono" }, S.run.run.run_id + ", " + S.run.discovery.knowledge + ", assessed as of " + S.run.discovery.as_of))));
  if (opts && opts.decision) p.append(candidateDecisionBox(e));
  return p;
}
function ledger(reqs, e) {
  return h("div", { class: "ledger" }, reqs.map(r => {
    const st = STATUS[r.status] || [r.status, "muted", null];
    const issue = e && e.mandatory_issues.find(m => m.requirement === r.id);
    const kind = r.protected && issue ? "protected" : st[2];
    return h("div", { class: "ledger-row s-" + r.status }, h("div", { class: "bar" }),
      h("div", { class: "rid" }, r.id, h("small", {}, r.stated_as)),
      h("div", { class: "body" },
        h("div", { class: "req" }, h("span", {}, r.text), h("span", { class: "tags" }, kind ? kindTag(kind) : null, h("span", { class: "tag " + st[1] }, st[0]), r.protected && kind !== "protected" ? kindTag("protected") : null)),
        r.path_label ? h("div", { class: "note" }, "How: " + r.path_label + (r.months !== null && r.months !== undefined ? ", " + r.months + " relevant months" : "")) : null,
        r.evidence.slice(0, 3).map(ev => h("blockquote", { class: "quote" }, h("span", { class: "where" }, ev.source.replace(/^candidate:/, "")), ev.text)),
        r.notes.length ? h("details", { class: "note" }, h("summary", {}, "Details"), r.notes.map(n => h("div", {}, n))) : null));
  }));
}
function candidateDecisionBox(e) {
  const dec = candDecision(e.candidate_id);
  const sel = h("select", {}, h("option", { value: "" }, "Choose what to do next"), S.state.candidate_dispositions.map(k => h("option", { value: k }, CAND_DISP[k] || k)));
  const why = h("textarea", { placeholder: "Why? (required) Do not paste contact details." });
  const mins = h("input", { type: "number", min: "0", step: "1", placeholder: "optional" });
  const box = h("div", { class: "decision" }, h("h4", {}, "Your decision about " + e.candidate_id),
    dec ? h("p", { class: "recorded" }, h("span", { class: "tag accent" }, CAND_DISP[dec.disposition]), " by " + dec.decided_by + " on " + dec.decided_at.slice(0, 10) + ": " + dec.rationale) : null,
    h("div", { class: "row" }, h("label", { class: "field" }, "Next step", sel), h("label", { class: "field w160" }, "Review minutes", mins)),
    h("label", { class: "field mt8" }, "Rationale", why), h("div", { class: "mt8" }, nameField()),
    h("div", { class: "row mt10" }, h("button", { class: "btn primary", onclick: () => guarded(async () => {
      if (!sel.value) throw new Error("Choose a next step");
      if (!needReviewer(box)) return;
      await api("POST", "sessions/" + S.session.id + "/runs/" + S.run.run.run_id + "/candidate-decisions",
        { candidate_id: e.candidate_id, disposition: sel.value, rationale: why.value, actor: reviewer(), review_minutes: mins.value || null });
      await reloadSession(); render(); toast("Decision recorded for " + e.candidate_id + ".");
    }) }, dec ? "Update decision" : "Record decision")),
    h("p", { class: "sub mt8" }, "Recorded on this computer only. Nothing is sent to the ATS or the candidate."));
  return box;
}

// ------------------------------------------------------------------ screening rules
function findingDecision(id) { return (S.session.decisions || []).find(d => d.finding_id === id); }
function findingLink(fid, label) { return h("a", { href: "#", onclick: (ev) => { ev.preventDefault(); S.selFinding = fid; S.tour.active = false; S.view = "rules"; render(true); } }, label || fid); }
function newlyCount(f) { const s = f.simulation || {}; return s.counts && s.proposed ? s.counts.newly_eligible_for_review : null; }
function viewRules() {
  const r = S.run.result;
  const root = h("div", {});
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Screening rules"),
    h("p", {}, "Where a supplied rule may exclude people whose evidence could meet the requirement, and what a proposed correction would change. Corrections are simulated, never applied."))));
  root.append(h("p", { class: "sub" }, "Rules analysed: " + cfgLabel(r.inputs.screening_configuration) + "."));
  if (!r.findings.length) {
    root.append(h("div", { class: "panel empty-state" }, h("h3", {}, "No screening-rule risks found"),
      h("p", {}, r.inputs.screening_configuration === "not_supplied" ? "No screening rules were supplied. Add the ATS configuration export to the requisition file and analyse again." : "The supplied rules are consistent with the posted requirements and policy.")));
    return root;
  }
  const cats = Object.keys(S.state.risk_categories || {});
  const count = (k) => r.findings.filter(f => f.risk_category === k).length;
  root.append(h("div", { class: "filters", role: "group", "aria-label": "Filter by type of risk" },
    [["all", "All (" + r.findings.length + ")"]].concat(cats.filter(k => count(k)).map(k => [k, riskLabel(k) + " (" + count(k) + ")"])).map(([k, label]) =>
      h("button", { "aria-pressed": S.levelFilter === k ? "true" : "false", onclick: () => { S.levelFilter = k; render(); } }, label))));
  const items = r.findings.filter(f => S.levelFilter === "all" || f.risk_category === S.levelFilter);
  const list = h("div", { class: "list", "aria-label": "Screening-rule findings" }, items.length ? items.map(f => {
    const dec = findingDecision(f.id), n = newlyCount(f);
    return h("button", { class: "item", "aria-pressed": S.selFinding === f.id ? "true" : "false", onclick: () => { S.selFinding = f.id; render(); } },
      h("div", { class: "line1" }, h("span", { class: "id" }, f.rule_id || f.requirement_id || f.candidate_id || "All"), scopeTag(f)),
      h("div", { class: "small" }, f.title),
      h("div", { class: "tags" }, f.risk_category ? h("span", { class: "tag " + (f.risk_category === "mandatory_protected" ? "bad" : "warn") }, riskLabel(f.risk_category)) : null,
        n !== null ? h("span", { class: "tag outline" }, n + " eligible if corrected (simulated)") : null,
        dec ? h("span", { class: "tag accent" }, FIND_DISP[dec.disposition] || dec.disposition) : null));
  }) : h("p", { class: "group-head" }, "No findings of this type."));
  root.append(h("div", { class: "split" }, list, h("div", { class: "detail" }, findingDetail(S.selFinding, { decision: true, simulation: true }))));
  return root;
}
function findingHeader(f) {
  return h("div", { class: "detail-head" }, h("div", {}, h("h2", { class: "fs19" }, f.title)),
    h("div", { class: "tags" }, scopeTag(f), f.risk_category ? h("span", { class: "tag " + (f.risk_category === "mandatory_protected" ? "bad" : "warn") }, riskLabel(f.risk_category)) : null));
}
function findingObserved(f) {
  const req = S.session.requisition;
  const reqObj = f.requirement_id && req.requirements.find(x => x.id === f.requirement_id);
  const ruleObj = f.rule_id && req.screening_rules.find(x => x.id === f.rule_id);
  const box = h("div", {});
  box.append(h("div", { class: "section" }, h("h4", {}, kindTag(f.risk_category === "mandatory_protected" ? "protected" : "observed"), " What the supplied materials show"), h("p", {}, f.observation),
    (reqObj || ruleObj) ? h("dl", { class: "kv mt8" },
      reqObj ? [h("dt", {}, "Requirement " + reqObj.id), h("dd", {}, reqObj.text + " (" + reqObj.stated_as + ")")] : null,
      ruleObj ? [h("dt", {}, "Supplied rule " + ruleObj.id), h("dd", {}, ruleObj.text + " — " + (ruleObj.action === "reject" ? "rejects automatically" : ruleObj.action.replace(/_/g, " ")))] : null,
      ruleObj ? [h("dt", {}, "Rule source"), h("dd", {}, cfgLabel(S.run.result.inputs.screening_configuration))] : null) : null));
  const affected = (f.affected_candidates || []).filter(c => entry(c));
  box.append(h("div", { class: "section" }, h("h4", {}, "Why it matters"), h("p", {}, f.expected_benefit),
    affected.length ? h("p", { class: "small" }, "Applies to " + plural(affected.length, "candidate") + " in this run: ", affected.map((c, i) => [i ? ", " : "", candLink(c)])) : null,
    h("p", { class: "sub" }, scopeOf(f)[1])));
  const ev = f.evidence.filter(x => !/^(requirement|rule):/.test(x.source));
  if (ev.length) box.append(h("details", { class: "section" }, h("summary", {}, "Evidence cited (" + ev.length + ")"), ev.slice(0, 8).map(x => h("blockquote", { class: "quote" }, h("span", { class: "where" }, (x.requirement ? x.requirement + " " : "") + x.source), x.text))));
  return box;
}
function findingDetail(fid, opts) {
  const r = S.run.result, f = r.findings.find(x => x.id === fid);
  if (!f) return h("div", { class: "panel empty" }, "Select a finding to see the rule, the evidence, the simulated correction, and the decision it needs.");
  const p = h("div", { class: "panel detail-body" });
  p.append(findingHeader(f), findingObserved(f));
  if (opts.simulation) add(p, beforeAfter(f));
  if (f.category !== "measured_impact") p.append(h("div", { class: "section" }, h("h4", {}, f.proposed_change ? "Proposed correction" : "Suggested action"),
    h("p", {}, f.proposed_action), h("p", { class: "sub" }, "Trade-off: " + f.tradeoffs)));
  if (f.limitations.length) p.append(h("div", { class: "section" }, h("h4", {}, kindTag("verify"), " What remains uncertain"), h("ul", { class: "plain small" }, f.limitations.map(l => h("li", {}, l)))));
  p.append(provenance(f));
  if (opts.decision && f.allowed_dispositions && f.allowed_dispositions.length) p.append(findingDecisionBox(f));
  return p;
}
function provenance(f) {
  const sim = f.simulation || {};
  return h("details", { class: "section tech" }, h("summary", {}, "Technical provenance"), h("dl", { class: "kv mt8" },
    h("dt", {}, "Finding"), h("dd", { class: "mono" }, f.id), h("dt", {}, "Check"), h("dd", { class: "mono" }, f.check),
    h("dt", {}, "Evidence level"), h("dd", {}, LEVEL[f.evidence_level] + "; confidence " + f.confidence),
    h("dt", {}, "Knowledge"), h("dd", { class: "mono" }, f.knowledge_version + (f.knowledge_refs.length ? " · " + f.knowledge_refs.join(", ") : "")),
    h("dt", {}, "Sources"), h("dd", { class: "mono" }, f.source_refs.map(s => s.kind + ":" + s.id).join(", ")),
    h("dt", {}, "Run"), h("dd", { class: "mono" }, S.run.run.run_id),
    sim.proposed ? [h("dt", {}, "Rule logic"), h("dd", {}, h("pre", { class: "out" }, "Supplied:\n" + JSON.stringify(sim.supplied || {}, null, 2) + "\n\nProposed (simulation only):\n" + JSON.stringify(sim.proposed, null, 2)))] : null));
}
function candLink(cid) {
  const e = entry(cid);
  const label = cid + (isPool(cid) ? " (talent pool)" : "");
  if (!e || !SURFACED.includes(e.group)) return h("span", {}, label);
  return h("a", { href: "#", onclick: (ev) => { ev.preventDefault(); S.selCandidate = cid; S.tour.active = false; S.view = "candidates"; render(true); } }, label);
}

// ------------------------------------------------------------------ before / after (recruiter-readable simulation)
function beforeAfter(f) {
  const sim = f.simulation;
  if (!sim) return null;
  const box = h("div", { class: "section ba" });
  if (!sim.evaluable) {
    box.append(h("h4", {}, kindTag("verify"), " Before and after"), h("p", {}, "This is a rule-level concern that can't be replayed against individual candidates: " + (sim.reason || "the supplied data does not allow it") + "."));
    return box;
  }
  if (sim.kind === "candidate") {
    box.append(h("h4", {}, kindTag("simulated"), " This candidate under the supplied rules and the proposed corrections"),
      h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Rule"), h("th", {}, "Today (supplied rule)"), h("th", {}, "With proposed corrections"))),
        h("tbody", {}, sim.rules.map(x => h("tr", {}, h("td", {}, h("b", {}, x.rule)), h("td", {}, outcomeTag(x.supplied), " " + x.supplied_reason), h("td", {}, outcomeTag(x.proposed), " " + x.proposed_reason)))))),
      h("p", { class: "sub mt8" }, "Result: " + sim.result + ". Passing the rules does not make anyone qualified."));
    return box;
  }
  const cat = (k) => sim.categories[k] || [];
  const pop = sim.population.applicants + sim.population.pool_records;
  box.append(h("h4", {}, kindTag("simulated"), " Before and after: what changes if " + (sim.rule || "the rule") + " were corrected"));
  box.append(h("div", { class: "compare" },
    h("div", { class: "side before" }, h("p", { class: "eyebrow" }, "Today, under the supplied rule"),
      h("b", { class: "num" }, cat("excluded_by_supplied_rule").length), h("span", {}, "of " + pop + " candidates checked are excluded by " + (sim.rule || "this rule"))),
    h("div", { class: "side after" }, h("p", { class: "eyebrow" }, sim.proposed ? "With the proposed correction (simulated, not applied)" : "No correction can be proposed"),
      sim.proposed ? [h("b", { class: "num" }, cat("newly_eligible_for_review").length), h("span", {}, "become eligible for human review — " + cat("would_pass_proposed_rule").length + " would pass this rule, but some still fail elsewhere")]
        : h("span", {}, "This rule protects a mandatory requirement."))));
  if (!sim.proposed) {
    add(box, bucket("still_fail_mandatory_requirement", "Excluded because they don't meet the mandatory requirement", "protected", cat("still_fail_mandatory_requirement"), sim,
      "No one is excluded for missing it."));
    return box;
  }
  const newly = cat("newly_eligible_for_review");
  box.append(h("div", { class: "bucket b-good" }, h("h5", {}, kindTag("simulated"), " Eligible for human review if corrected (" + newly.length + ")"),
    newly.length ? h("ul", { class: "plain" }, newly.map(c => eligibleRow(c, sim))) : h("p", { class: "sub" }, "No one in this run becomes eligible from this correction alone.")));
  add(box, bucket("still_fail_mandatory_requirement", "Still fail a mandatory requirement", "protected", cat("still_fail_mandatory_requirement"), sim,
    "No one in this simulation bypasses a mandatory requirement."));
  add(box, bucket("still_fail_other_supplied_rules", "Relevant evidence, but still fail other supplied rules", "simulated", cat("still_fail_other_supplied_rules"), sim));
  add(box, bucket("relevance_not_established", "Would pass the rule, but their evidence doesn't support the role", "verify", cat("relevance_not_established"), sim));
  add(box, bucket("evidence_insufficient", "Can't tell from the evidence supplied", "verify", cat("evidence_insufficient"), sim));
  box.append(h("p", { class: "sub mt8" }, "Passing a simulated rule never makes anyone qualified. Talent-pool records did not apply to this role; their results are hypothetical."));
  box.append(h("details", { class: "mt8" }, h("summary", {}, "Simulation limits and per-candidate notes"),
    h("ul", { class: "plain small" }, sim.limitations.map(l => h("li", {}, l))),
    h("ul", { class: "plain small mt8" }, Object.entries(sim.notes || {}).map(([c, n]) => h("li", {}, h("b", {}, c + " "), n)))));
  return box;
}
function outcomeTag(v) { return h("span", { class: "tag " + (v === false ? "bad" : v ? "ok" : "warn") }, v === false ? "Excluded" : v ? "Passes" : "Can't evaluate"); }
function bucket(key, title, kind, ids, sim, emptyText) {
  if (!ids.length && !emptyText) return null;
  return h("div", { class: "bucket" }, h("h5", {}, kindTag(kind), " " + title + " (" + ids.length + ")"),
    ids.length ? h("p", { class: "small" }, ids.map((c, i) => [i ? ", " : "", candLink(c), sim.sources && sim.sources[c] === "pool" ? h("span", { class: "sub" }, " hypothetical") : null])) : h("p", { class: "sub" }, emptyText));
}
function eligibleRow(cid, sim) {
  const e = entry(cid);
  const basis = (sim.eligibility_basis || {})[cid];
  if (!e) return h("li", {}, cid);
  return h("li", {}, h("details", { class: "elig" }, h("summary", {}, h("b", {}, cid), " ", h("span", { class: "tag " + (e.group === "direct" ? "ok" : "warn") }, GROUPS[e.group] ? GROUPS[e.group][0] : e.group),
      isPool(cid) ? h("span", { class: "sub" }, " talent pool, hypothetical") : null),
    h("ul", { class: "plain small" }, e.why.slice(1).map(w => h("li", {}, w)),
      basis ? h("li", {}, "Eligible " + basis + ".") : null,
      e.unverified.length ? h("li", {}, kindTag("verify"), " Verify: " + e.unverified.map(u => u.requirement + " (" + u.reason + ")").join("; ")) : null),
    h("p", { class: "small" }, candLink(cid), " — open their evidence")));
}

// ------------------------------------------------------------------ finding decisions
function findingDecisionBox(f, opts) {
  const dec = findingDecision(f.id);
  const applied = f.disposition && f.disposition.status !== "pending";
  const history = (S.session.decision_history || []).filter(x => x.kind === "finding" && x.id === f.id);
  const sel = h("select", {}, h("option", { value: "" }, "Choose a decision"), f.allowed_dispositions.map(k => h("option", { value: k }, FIND_DISP[k] || k)));
  const why = h("textarea", { placeholder: "Why? (required) For example: the posting accepts production operations experience, so the rule should too." });
  const box = h("div", { class: "decision" }, h("h4", {}, "Your decision"),
    dec ? h("p", { class: "recorded" }, h("span", { class: "tag accent" }, FIND_DISP[dec.disposition] || dec.disposition), " by " + dec.decided_by + " on " + dec.decided_at.slice(0, 10) + ": " + dec.rationale,
      applied ? null : h("span", { class: "sub" }, " — included in the analysis the next time it is run.")) : null,
    h("label", { class: "field" }, "Decision", sel), h("label", { class: "field mt8" }, "Rationale", why), h("div", { class: "mt8" }, nameField()),
    h("div", { class: "row mt10" }, h("button", { class: "btn primary", onclick: () => guarded(async () => {
      if (!sel.value) throw new Error("Choose a decision");
      if (!why.value.trim()) { why.focus(); throw new Error("Add a rationale: it is what lets a colleague or auditor understand the decision later"); }
      if (!needReviewer(box)) return;
      await api("POST", "sessions/" + S.session.id + "/runs/" + S.run.run.run_id + "/finding-decisions",
        { finding_id: f.id, disposition: sel.value, rationale: why.value, actor: reviewer() });
      await reloadSession();
      if (opts && opts.after) opts.after(); else { render(); toast("Decision recorded."); }
      announce("Decision recorded.");
    }) }, dec ? "Update decision" : "Record decision")),
    history.length ? h("details", { class: "mt10" }, h("summary", {}, "Decision history (" + history.length + ")"),
      h("ul", { class: "plain small" }, history.slice().reverse().map(x => h("li", {}, when(x.decided_at) + " " + (FIND_DISP[x.disposition] || x.disposition) + " by " + x.decided_by + " in run " + x.run_id + ": " + x.rationale)))) : null,
    h("p", { class: "sub mt8" }, "Your decision records intent. Nothing is changed in the ATS, in the supplied rules or in the knowledge."));
  return box;
}

// ------------------------------------------------------------------ decisions & export
const EXPORTS_MAIN = [["review-list.csv", "Candidate review list", "One row per candidate to review, with the evidence summary, what to verify and your decision. Opens in any spreadsheet."],
  ["screening-risks.yaml", "Screening-rule findings", "Each rule risk with its simulated correction and your decision, for the person who owns the ATS configuration."],
  ["decision-history.jsonl", "Decision history", "Every decision ever recorded, with who made it, when, and the run and inputs it was based on."]];
const EXPORTS_MORE = [["report.html", "Full report (HTML)"], ["report.md", "Full report (Markdown)"], ["review-list.yaml", "Review list (YAML)"], ["decisions.yaml", "Finding decisions (YAML)"],
  ["review-decisions.yaml", "Candidate decisions (YAML)"], ["changes.yaml", "Accepted configuration changes"], ["findings.json", "Findings (JSON)"], ["discovery.json", "Discovery (JSON)"],
  ["bundle.zip", "Everything, with knowledge snapshot (ZIP)"]];
function exportPanel(compact) {
  return h("section", { class: "panel" }, h("h3", {}, "Take it with you"),
    h("p", { class: "sub" }, "Exports reflect the analysis run on " + when(S.run.run.run_at) + "; decision files include everything recorded so far."),
    h("div", { class: "exports" }, EXPORTS_MAIN.map(([name, label, help]) => h("div", { class: "exp" },
      h("button", { class: "btn" + (name === "review-list.csv" ? " primary" : ""), onclick: () => guarded(() => download(name)) }, "Download " + label.toLowerCase()), h("p", { class: "sub" }, help)))),
    h("details", { class: "mt10" }, h("summary", {}, "More formats"), h("div", { class: "row mt8" }, EXPORTS_MORE.map(([name, label]) => h("button", { class: "btn", onclick: () => guarded(() => download(name)) }, label)))),
    compact ? null : h("p", { class: "sub mt10" }, "How teams use these: share the review list with the hiring team and work it in your ATS as usual; send the screening-rule findings to whoever maintains the knockout questions; keep the decision history with the requisition record."));
}
function viewDecisions() {
  const s = S.session, run = S.run.run, r = S.run.result, d = S.run.discovery;
  const root = h("div", { class: "stack" });
  root.append(h("div", { class: "view-head" }, h("div", { class: "grow" }, h("h2", {}, "Decisions & export"),
    h("p", {}, "Every decision is attributed and kept with the run it was based on. Decisions carry over to later analyses while their candidates and findings still exist."))));
  const pendingC = d.entries.filter(e => SURFACED.includes(e.group) && !candDecision(e.candidate_id)).length;
  const pendingF = r.findings.filter(f => (f.allowed_dispositions || []).length && !findingDecision(f.id)).length;
  const newSince = s.decisions.filter(x => x.decided_at > run.run_at).length + s.review_decisions.filter(x => x.decided_at > run.run_at).length;
  root.append(h("div", { class: "counts" },
    h("div", {}, h("b", {}, pendingC), h("span", {}, "candidates awaiting a decision")),
    h("div", {}, h("b", {}, pendingF), h("span", {}, "findings awaiting a decision")),
    h("div", {}, h("b", {}, s.decisions.length + s.review_decisions.length), h("span", {}, "decisions recorded"))));
  if (newSince) root.append(h("div", { class: "banner info" }, plural(newSince, "decision was", "decisions were") + " recorded after this analysis ran, so the analysis and report don't reflect them yet. ", rerunButton("Update the analysis")));
  const co = run.carried_over;
  if (co.finding_decisions_stale.length || co.candidate_decisions_stale.length) root.append(h("div", { class: "banner" },
    "Some earlier decisions are kept but no longer apply, because the finding or candidate they were about no longer appears in this analysis: " + co.finding_decisions_stale.concat(co.candidate_decisions_stale).join(", ") + "."));
  const changed = co.decisions_with_changed_context || [];
  if (changed.length) root.append(h("div", { class: "banner" }, h("b", {}, "Please look at these decisions again. "),
    "They still apply, but something they were based on has changed since they were made:",
    h("ul", { class: "plain small" }, changed.map(c => h("li", {}, c.kind + " " + c.id + ": " + c.reasons.map(x => x.replace(/^knowledge changed.*/, "the knowledge used for matching was updated").replace("inputs changed", "the input files changed")).join("; "))))));
  root.append(exportPanel());
  const noDec = h("p", { class: "sub" }, "No decisions yet. Open a candidate or a screening-rule finding to record one.");
  root.append(h("section", { class: "panel" }, h("h3", {}, "Candidate decisions"), s.review_decisions.length ? decisionsTable(s.review_decisions.map(x => [candLink(x.candidate_id), CAND_DISP[x.disposition] || x.disposition, x.decided_by, when(x.decided_at), x.rationale]),
    ["Candidate", "Next step", "By", "When", "Rationale"]) : noDec));
  const fTitle = (id) => { const f = r.findings.find(x => x.id === id); return f ? findingLink(id, f.title) : h("span", { class: "mono" }, id + " (not in this run)"); };
  root.append(h("section", { class: "panel" }, h("h3", {}, "Screening-rule decisions"), s.decisions.length ? decisionsTable(s.decisions.map(x => [fTitle(x.finding_id), FIND_DISP[x.disposition] || x.disposition, x.decided_by, when(x.decided_at), x.rationale]),
    ["Finding", "Decision", "By", "When", "Rationale"]) : noDec.cloneNode(true)));
  if (r.measurement) root.append(h("section", { class: "panel" }, h("h3", {}, "Outcomes"), outcomes(r.measurement)));
  root.append(h("details", { class: "panel" }, h("summary", {}, "Runs and reproducibility"),
    h("p", { class: "sub mt8" }, "Each run stores input fingerprints, the knowledge documents used and the decisions applied. Verifying re-runs it from those and compares the outputs byte for byte."),
    h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, h("th", {}, "Run"), h("th", {}, "When"), h("th", {}, "Knowledge"), h("th", {}, ""))),
      h("tbody", {}, s.runs.slice().reverse().map(x => {
        const v = S.verify[x.run_id];
        return h("tr", {}, h("td", { class: "mono" }, x.run_id), h("td", {}, when(x.run_at) + " by " + x.run_by), h("td", { class: "mono" }, x.knowledge.fingerprint),
          h("td", {}, h("button", { class: "btn", onclick: () => guarded(async () => {
            S.verify[x.run_id] = await api("POST", "sessions/" + s.id + "/runs/" + x.run_id + "/verify", { actor: runActor() || "workbench user" }); render();
          }) }, "Verify"), v ? h("div", { class: "mt6" }, h("span", { class: "tag " + (v.reproduced ? "ok" : "bad") }, v.reproduced ? "Reproduced exactly" : "Not reproduced"),
            h("ul", { class: "plain small" }, v.checks.filter(c => !c.ok).map(c => h("li", {}, c.check + (c.detail ? ": " + c.detail : ""))))) : null));
      }))))));
  if (S.state.evaluation_available && !isDemo()) root.append(evaluationPanel());
  return root;
}
function rerunButton(label, after) {
  const b = h("button", { class: "btn", onclick: () => guarded(async () => {
    if (!runActor()) return needReviewer();
    b.disabled = true; b.textContent = "Updating…";
    let nr;
    try { nr = await api("POST", "sessions/" + S.session.id + "/runs", { knowledge: S.run.run.knowledge.spec, actor: runActor() }); }
    finally { b.disabled = false; b.textContent = label; }
    await openSession(S.session.id, nr.run_id);
    if (after) after(nr); else render();
    toast("Analysis updated. " + (nr.carried_over.finding_decisions_applied.length + nr.carried_over.candidate_decisions_applied.length) + " decision(s) applied.");
  }) }, label);
  return b;
}
function decisionsTable(rows, head) {
  return h("div", { class: "tbl" }, h("table", {}, h("thead", {}, h("tr", {}, head.map(x => h("th", {}, x)))), h("tbody", {}, rows.map(r => h("tr", {}, r.map(c => h("td", {}, c instanceof Node ? c : String(c))))))));
}
function outcomes(m) {
  const me = m.measured;
  return h("div", {},
    h("p", { class: "sub" }, "Comparison method: " + m.comparison_method),
    h("h4", {}, kindTag("observed"), " Measured"),
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
  return h("details", { class: "panel" }, h("summary", {}, "For knowledge administrators: evaluation"),
    h("p", { class: "sub mt8" }, "After editing a knowledge document, run the labelled evaluation suite and compare against the version in use. Fixture results are synthetic and are not a measure of real-world accuracy."),
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
  toast("Downloaded " + (m ? m[1] : name) + ".");
}

// ------------------------------------------------------------------ guided tour (demo)
const TOUR = [
  ["What might we be missing?", "The value at a glance"],
  ["Understand the role", "What the analysis uses"],
  ["Discover candidates", "Evidence worth a second look"],
  ["Inspect a screening risk", "A rule narrower than the job"],
  ["Compare the correction", "Before and after, simulated"],
  ["Make a human decision", "Attributed, with a rationale"],
  ["See the result and take it with you", "Exports for your workflow"],
];
function startTour(step) { S.tour = { active: true, step: step || 0 }; render(true); }
function tourGo(step) { S.tour.step = Math.max(0, Math.min(TOUR.length - 1, step)); render(true); announce("Step " + S.tour.step + " of " + (TOUR.length - 1) + ": " + TOUR[S.tour.step][0]); }
function endTour(view) { S.tour.active = false; S.view = view || "overview"; render(true); }
function renderTourNav(nav) {
  nav.append(h("p", { class: "tour-title" }, "Guided demo"));
  nav.append(h("ol", { class: "tour-steps" }, TOUR.map(([t, sub], i) => h("li", {}, h("button", { "aria-current": S.tour.step === i ? "step" : false, class: i < S.tour.step ? "done" : "",
    onclick: () => tourGo(i) }, h("span", { class: "n" }, i === 0 ? "★" : String(i)), h("span", {}, t, h("small", {}, sub)))))));
  nav.append(h("button", { class: "linkish mt12", onclick: () => endTour("overview") }, "Skip the tour and explore on my own"));
}
function viewTour() {
  const step = S.tour.step, sel = S.run.guide.tour;
  const f = sel.finding_id && S.run.result.findings.find(x => x.id === sel.finding_id);
  const e = sel.candidate_id && entry(sel.candidate_id);
  const root = h("div", { class: "tour" });
  root.append(h("div", { class: "progress", role: "progressbar", "aria-label": "Guided demo progress", "aria-valuemin": "0", "aria-valuemax": String(TOUR.length - 1), "aria-valuenow": String(step) },
    h("div", { class: "bar w" + Math.round(step / (TOUR.length - 1) * 6) })));
  const coach = (title, value, ...kids) => h("section", { class: "coach" }, h("p", { class: "eyebrow" }, step === 0 ? "Guided demo · " + S.session.title : "Step " + step + " of " + (TOUR.length - 1)),
    h("h2", {}, title), h("p", { class: "lede" }, value), kids);
  let body;
  if (step === 0) {
    body = [coach("What might we be missing for this role?", "This is a real analysis of a fictional Senior SRE requisition: " + S.run.guide.summary.candidates_considered + " de-identified candidate records checked against the posted requirements and the ATS knockout rules. Here is what it found."),
      viewOverview(true)];
  } else if (step === 1) {
    body = [coach("Understand the role", "Everything starts from the requirements the hiring team actually posted. The analysis compares them with the screening rules the ATS applies, under your employer policy — nothing else."),
      viewRole(true)];
  } else if (step === 2) {
    body = e ? [coach("Discover candidates", "Here is " + e.candidate_id + ". " + (e.screening.excluded_by && e.screening.excluded_by.length ? "The current rules rejected them, " : "") +
        "yet their record supports every required requirement — part of it through related experience described in different words. Look at what supports review, what's still unknown, and what you'd verify."),
      candidateDetail(e.candidate_id, { decision: false })]
      : [coach("Discover candidates", "This sample has no candidate evidence, so there is no one to show. With applicants or a talent pool, this step opens a representative candidate."), h("div", {})];
  } else if (step === 3) {
    body = f ? [coach("Inspect a screening risk", "Why was " + (e ? e.candidate_id : "that candidate") + " kept out? One reason is this " + scopeOf(f)[0].toLowerCase() + " finding: a supplied rule that is narrower than the requirement it is meant to check."),
      h("div", { class: "panel detail-body" }, findingHeader(f), findingObserved(f), legend())]
      : [coach("Inspect a screening risk", "No screening-rule risks were found for this sample."), h("div", {})];
  } else if (step === 4) {
    body = f ? [coach("Compare the correction", "What would change if the rule matched the requirement? The correction is replayed on the same candidates — nothing in the ATS, the rules or the knowledge changes. Being eligible means a human should look, not that the person is qualified."),
      h("div", { class: "panel detail-body" }, h("h3", {}, f.title), beforeAfter(f), h("div", { class: "section" }, h("h4", {}, "The proposed correction"), h("p", {}, f.proposed_action), h("p", { class: "sub" }, "Trade-off: " + f.tradeoffs)), legend())]
      : [coach("Compare the correction", "There is no correction to simulate for this sample."), h("div", {})];
  } else if (step === 5) {
    body = f && f.allowed_dispositions.length ? [coach("Make a human decision", "The product never changes a rule or a candidate's status. You decide — accept the concern, reject it, defer it, or ask for evidence — and say why. The rationale and your name are stored with the exact run and inputs the decision was based on."),
      h("div", { class: "panel detail-body" }, h("h3", {}, f.title), h("p", { class: "sub" }, f.proposed_action), findingDecisionBox(f, { after: () => { tourGo(6); toast("Decision recorded."); } }))]
      : [coach("Make a human decision", "No decision is needed for this sample."), h("div", {})];
  } else {
    body = [coach("See the result and take it with you", "Your decision is part of the record now: who decided, why, and on which analysis. Export what your team needs and keep working in your ATS as usual."),
      resultStep(f), exportPanel(), validationExplainer(),
      h("section", { class: "panel finish" }, h("h3", {}, "That's the whole loop"),
        h("p", {}, "Find candidates the process may be missing, understand why, and decide what to do — with evidence."),
        h("div", { class: "row mt10" }, h("button", { class: "btn primary", onclick: () => endTour("candidates") }, "Explore this sample on my own"),
          h("button", { class: "btn", onclick: () => { goHome(); S.view = "upload"; } }, "Review my own requisition")))];
  }
  add(root, ...body);
  root.append(h("nav", { class: "tour-nav", "aria-label": "Guided demo navigation" },
    step > 0 ? h("button", { class: "btn", onclick: () => tourGo(step - 1) }, "← Back") : h("span", {}),
    h("span", { class: "grow" }),
    step < TOUR.length - 1 ? h("button", { class: "btn primary", onclick: () => tourGo(step + 1) }, step === 0 ? "Start: understand the role →" : "Next: " + TOUR[step + 1][0].toLowerCase() + " →")
      : h("button", { class: "btn primary", onclick: () => endTour("overview") }, "Finish the tour")));
  return root;
}
function resultStep(f) {
  const dec = f && findingDecision(f.id);
  const hist = f ? (S.session.decision_history || []).filter(x => x.kind === "finding" && x.id === f.id) : [];
  const last = hist[hist.length - 1];
  if (!dec) return h("section", { class: "panel" }, h("h3", {}, "No decision recorded yet"),
    h("p", {}, "Go back one step to record a decision. Nothing is recorded until you choose to."), h("button", { class: "btn", onclick: () => tourGo(5) }, "← Make the decision"));
  const applied = S.run.run.carried_over.finding_decisions_applied.includes(f.id);
  return h("section", { class: "panel recorded-card" }, h("h3", {}, "Recorded decision"),
    h("p", { class: "big" }, h("span", { class: "tag accent" }, FIND_DISP[dec.disposition] || dec.disposition), " " + f.title),
    h("blockquote", { class: "quote" }, h("span", { class: "where" }, "Rationale"), dec.rationale),
    h("dl", { class: "kv mt10" },
      h("dt", {}, "Decided by"), h("dd", {}, dec.decided_by + ", " + when(dec.decided_at)),
      h("dt", {}, "Based on"), h("dd", {}, "Analysis run " + (last ? last.run_id : S.run.run.run_id) + " · knowledge " + (last ? last.knowledge : S.run.run.knowledge.fingerprint)),
      h("dt", {}, "Evidence"), h("dd", {}, "Rule " + (f.rule_id || "—") + " and requirement " + (f.requirement_id || "—") + "; candidates affected: ", ((f.simulation || {}).categories || {}).newly_eligible_for_review ? f.simulation.categories.newly_eligible_for_review.map((c, i) => [i ? ", " : "", candLink(c)]) : "—"),
      h("dt", {}, "Input fingerprint"), h("dd", { class: "mono" }, last ? short(last.inputs_sha256, 16) : "—")),
    applied ? h("p", { class: "banner info mt10" }, "The current analysis already includes this decision.")
      : h("div", { class: "banner info mt10" }, "The analysis you're looking at was run before this decision. Update it so the report and exports reflect the decision. ",
        rerunButton("Update the analysis", () => { render(); })));
}
function validationExplainer() {
  const v = S.valSample;
  const box = h("details", { class: "panel", open: !!S.valOpen, ontoggle: (ev) => {
      S.valOpen = ev.target.open;
      if (ev.target.open && !S.valSample) guarded(async () => { S.valSample = await api("GET", "validation-sample"); render(); });
    } },
    h("summary", {}, "How would we know it works for your roles?"),
    h("p", { class: "mt8" }, "In a pilot, recruiters who have not seen the product's output review a sample of real, de-identified candidates and findings. The validation report then counts — with numerators, denominators and unknowns kept visible:"),
    h("ul", { class: "plain small" }, h("li", {}, "relevant candidates surfaced and still missed, and irrelevant candidates surfaced;"),
      h("li", {}, "screening-rule findings confirmed, rejected or left unreviewed by independent reviewers;"),
      h("li", {}, "any case where a mandatory requirement or policy would have been bypassed (reported individually, never averaged away);"),
      h("li", {}, "recruiter time and decisions, only where they were actually measured.")),
    h("p", { class: "sub" }, "No real-world results exist for this product yet; none are shown here."));
  if (v) box.append(h("div", { class: "synthetic mt10" }, h("p", { class: "eyebrow" }, v.label),
    h("p", { class: "small" }, "The same measurement, run on the included synthetic fixtures (labels written alongside the sample data). It shows how results are reported — not how well the product works:"),
    h("ul", { class: "plain small" },
      h("li", {}, "Findings independently confirmed: " + v.metrics.F1_confirmed.numerator + " of " + v.metrics.F1_confirmed.denominator + "; not reviewed: " + v.metrics.F5_unreviewed.numerator + " (never counted as confirmed)"),
      h("li", {}, "Candidates without a resolved label: " + (v.coverage.labels.unassessable + v.coverage.labels.unresolved + v.coverage.labels.unreviewed) + " (kept out of every rate)"),
      h("li", {}, "Mandatory or policy violations: " + (v.violations_occurred ? "yes — listed individually" : "none occurred"))),
    h("p", { class: "sub mono" }, "Dataset " + v.dataset_id + " · evaluation " + v.evaluation_contract + " · knowledge " + v.knowledge)));
  return box;
}

// ------------------------------------------------------------------ data
async function refreshState() { S.state = await api("GET", "state"); render(); }
async function reloadSession() { S.session = await api("GET", "sessions/" + S.session.id); }
async function openSession(id, runId) {
  S.session = await api("GET", "sessions/" + id);
  const rid = runId || (S.session.runs.length ? S.session.runs[S.session.runs.length - 1].run_id : null);
  S.run = rid ? await api("GET", "sessions/" + id + "/runs/" + rid) : null;
  S.state = await api("GET", "state");
  if (!S.run) { S.view = "role"; S.tour.active = false; }
  if (S.run) {
    const sel = S.run.guide.tour;
    const firstCand = sel.candidate_id || ((S.run.discovery.entries.find(e => SURFACED.includes(e.group)) || {}).candidate_id) || null;
    if (!S.run.discovery.entries.some(e => e.candidate_id === S.selCandidate)) S.selCandidate = firstCand;
    if (!S.run.result.findings.some(f => f.id === S.selFinding)) S.selFinding = sel.finding_id || (S.run.result.findings[0] || {}).id || null;
  }
}

S.reviewer = (() => { try { return localStorage.getItem("sa-reviewer") || ""; } catch (e) { return ""; } })();
guarded(refreshState);
