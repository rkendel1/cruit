"""Markdown rendering of design-partner validation results (`sa measure`, `sa measure-compare`)."""

from __future__ import annotations

from typing import Any


def _r(x: dict[str, Any] | None) -> str:
    if not x:
        return "—"
    if x["rate"] is None:
        return f"{x['numerator']} / {x['denominator']} (no eligible items)"
    return f"{x['numerator']} / {x['denominator']} ({x['rate']:.0%})"


def _ids(xs: list[str]) -> str:
    return ", ".join(xs) if xs else "none"


def render_validation_markdown(res: dict[str, Any]) -> str:
    m = res["metrics"]
    cov, disc, base, risk, vio, agr, wf = (m["coverage"], m["discovery"], m["baseline"], m["screening_risks"],
                                          m["violations"], m["agreement"], m["workflow"])
    ds = res["dataset"]
    L = [f"# Validation result `{res['result_id']}` — {ds['id']}", "", f"> **{res['label']}**", ""]
    L += ["| Provenance | |", "|---|---|",
          f"| Dataset | `{ds['id']}` v{ds['version']} ({ds['kind'].replace('_', '-')}), contract v{ds['contract_version']}, provider {ds['provider']}, collected {ds['collected_at']} |",
          f"| Dataset inputs sha256 | `{ds['sha256'][:16]}…` |",
          f"| Engine | {res['engine_version']} |",
          f"| Knowledge | `{res['knowledge']['fingerprint']}` |",
          f"| Evaluation contract | {res['evaluation_contract']} |",
          f"| Retention | delete after {res['retention']['delete_after']} ({res['retention']['deletion'].replace('_', ' ')}) |", ""]

    # 1 coverage
    lab = cov["labels"]
    L += ["## 1. Dataset coverage and missing labels", "",
          f"{cov['cases']} case(s), {cov['candidates']} candidate record(s), {cov['screening_risk_findings']} screening-risk finding(s).", "",
          "| Relevance label (independent review) | Candidates |", "|---|---|",
          f"| Relevant | {lab['relevant']} |", f"| Not relevant | {lab['not_relevant']} |",
          f"| Unassessable from supplied evidence | {lab['unassessable']} |",
          f"| Reviewers disagree, not adjudicated (unresolved) | {lab['unresolved']} |",
          f"| Not reviewed | {lab['unreviewed']} |", "",
          f"- Cases without a baseline: {_ids(cov['cases_without_baseline'])}",
          f"- Screening-risk findings not reviewed: {cov['findings_unreviewed']}",
          "- Unknown, unresolved and unreviewed labels are never counted as relevant or irrelevant.", ""]

    # 2 baseline vs SA
    L += ["## 2. Existing process vs. Screening Assurance (side by side)", "",
          "The baseline column is what the existing screening process did, as recorded by the partner. The Screening "
          "Assurance column is a deterministic re-run of the product on the same inputs. Simulated corrections are not "
          "changes to the employer's process.", ""]
    for c in res["cases"]:
        L += [f"### {c['case_id']} · {c['requisition_id']} · {c['scenario']}", "",
              f"Baseline source: {c['baseline']['baseline_source'].replace('_', ' ')}. As of {c['as_of']}. "
              f"Policy {c['policy_version']}. Rules {', '.join(c['screening_rules'])} ({c['screening_configuration'].replace('_', ' ')}).", "",
              "| Candidate | Baseline outcome (basis) | Screening Assurance group | Independent label |", "|---|---|---|---|"]
        for cid in sorted(c["product_groups"]):
            b = c["baseline_outcomes"].get(cid)
            bo = "not available" if c["baseline"]["baseline_source"] == "not_available" else (
                f"{b['outcome'].replace('_', ' ')} ({b['basis']})" if b else "not recorded")
            if b and b.get("excluded_by_rule"):
                bo += f", rule {b['excluded_by_rule']}"
            L.append(f"| {cid} | {bo} | {c['product_groups'][cid].replace('_', ' ')} | {c['labels'][cid].replace('_', ' ')} |")
        L.append("")

    # 3 discovery
    L += ["## 3. Discovery metrics", "", "| Metric | Value |", "|---|---|",
          f"| D1 Relevant candidates surfaced for human review | {_r(disc['D1_relevant_surfaced'])} |",
          f"| D2 Relevant candidates still missed | {_r(disc['D2_relevant_missed'])} |",
          f"| D3 Irrelevant candidates surfaced | {_r(disc['D3_irrelevant_surfaced'])} |",
          f"| D4 Surfaced, relevance not established | {_r(disc['D4_surfaced_relevance_unknown'])} |",
          f"| D5 Surfaced results requiring human verification | {_r(disc['D5_requires_verification'])} |",
          f"| Relevant but blocked by authorization or evidence age (not a miss) | {disc['relevant_blocked_by_authorization']} |",
          f"| Already in active ATS review (excluded) | {disc['already_in_active_review']} |", "",
          "| Baseline comparison | Value |", "|---|---|",
          f"| B1 Relevant candidates the existing process excluded (observed) | {_r(base['B1_baseline_missed_relevant'])} |",
          f"| B1 inferred only (not counted above) | {base['B1_inferred_only']} |",
          f"| B2 Of those, surfaced by Screening Assurance | {_r(base['B2_recovered_by_product'])} |",
          f"| B3 Of those, still missed by Screening Assurance | {_r(base['B3_still_missed_by_product'])} |",
          f"| Pool records that never applied (no baseline applies) | {base['baseline_not_applicable']} |",
          f"| Candidates with unknown baseline outcome | {base['baseline_unknown']} |", ""]
    L += ["| Case | Relevant surfaced | Relevant missed | Irrelevant surfaced | Relevance unknown | Unassessable |", "|---|---|---|---|---|---|"]
    for c in res["cases"]:
        d = c["discovery"]
        unass = [x for x in c["unresolved_candidates"] if c["labels"][x] == "unassessable"]
        L.append(f"| {c['case_id']} | {_ids(d['relevant_surfaced'])} | {_ids(d['relevant_missed'])} | {_ids(d['irrelevant_surfaced'])} | "
                 f"{_ids(d['surfaced_relevance_unknown'])} | {_ids(unass)} |")
    L.append("")

    # 4 screening risks
    L += ["## 4. Screening-risk metrics", "",
          "Findings are matched to independent reviews by check and rule/requirement/candidate. Product findings are never "
          "their own ground truth: an unreviewed finding is not a confirmed finding.", "",
          "| Metric | Value |", "|---|---|",
          f"| F1 Findings independently confirmed | {_r(risk['F1_confirmed'])} |",
          f"| F2 Findings rejected (unsupported or irrelevant) | {_r(risk['F2_rejected'])} |",
          f"| F3 Deferred or needing more evidence | {_r(risk['F3_deferred_or_needs_evidence'])} |",
          f"| F4 Reviewer disagreement, unresolved | {_r(risk['F4_unresolved'])} |",
          f"| F5 Not reviewed | {_r(risk['F5_unreviewed'])} |",
          f"| F6 Corrections that reveal relevant candidates | {_r(risk['F6_corrections_reveal_relevant'])} |",
          f"| F7 Corrections that surface irrelevant candidates | {_r(risk['F7_corrections_surface_irrelevant'])} |",
          f"| Newly eligible candidates with no resolved label | {risk['corrections_relevance_unknown']} |",
          f"| F8 Exclusion cause cannot be established (candidates + non-evaluable simulations) | {risk['F8_exclusion_cause_unknown']} |",
          f"| F9 Findings without a verified baseline | {_r(risk['F9_without_verified_baseline'])} |",
          f"| Reviews for findings the product did not produce | {risk['reviews_for_findings_not_produced']} |", ""]
    for c in res["cases"]:
        rows = c["screening_risks"]["findings"]
        if not rows:
            continue
        L += [f"### {c['case_id']} findings", "", "| Finding | Check | Rule / requirement / candidate | Review | Baseline verified |", "|---|---|---|---|---|"]
        for f in rows:
            rv = f["review"]
            if rv["status"] == "unreviewed":
                rtxt = "not reviewed"
            elif rv["status"] == "unresolved":
                rtxt = "unresolved disagreement (" + ", ".join(rv["values"]) + ")"
            else:
                rtxt = f"{rv['value'].replace('_', ' ')} ({rv['status'].replace('_', ' ')})"
            ref = " / ".join(x for x in (f["rule"], f["requirement"], f["candidate"]) if x) or "—"
            L.append(f"| `{f['finding_id']}` | {f['check']} | {ref} | {rtxt} | {'yes' if f['baseline_verified'] else 'no'} |")
        sr = c["screening_risks"]
        L += ["", f"- Corrections reveal relevant: {_ids(sr['corrections_reveal_relevant'])}; surface irrelevant: "
              f"{_ids(sr['corrections_surface_irrelevant'])}; relevance unknown: {_ids(sr['corrections_relevance_unknown'])}",
              f"- Exclusion cause unknown: {_ids(sr['exclusion_cause_unknown'])}", ""]

    # 5 violations
    L += ["## 5. Mandatory-requirement and policy violations", ""]
    if not vio["occurred"]:
        L.append("**No mandatory-requirement or policy violations occurred** in this dataset.")
    else:
        L.append(f"**Violations occurred: {vio['V1_mandatory']} mandatory, {vio['V2_policy']} policy.** Each is listed below; "
                 "they are not offset by any other metric.")
    L.append("")
    for c in res["cases"]:
        for kind in ("mandatory", "policy"):
            for v in c["violations"][kind]:
                L.append(f"- {c['case_id']} [{kind}] {v}")
    unv = [f"{c['case_id']}: {x}" for c in res["cases"] for x in c["violations"]["mandatory_unverified"]]
    L += ["", f"Mandatory requirements that reviewers could not verify, or disagreed on, for surfaced/newly eligible candidates "
          f"(neither violation nor pass): {_ids(unv)}", ""]

    # 6 agreement
    L += ["## 6. Reviewer agreement and adjudication", "", "| | Candidates | Findings |", "|---|---|---|",
          f"| Items with two or more reviews | {agr['candidates_with_multiple_reviews']} | {agr['findings_with_multiple_reviews']} |",
          f"| Reviewers agreed | {agr['candidate_agreements']} | {agr['finding_agreements']} |",
          f"| Reviewers disagreed | {agr['candidate_disagreements']} | {agr['finding_disagreements']} |",
          f"| Disagreements adjudicated | {agr['candidate_disagreements_adjudicated']} | {agr['finding_disagreements_adjudicated']} |", "",
          f"Candidate assessments made without seeing product output: {agr['blind_candidate_reviews']}.", ""]
    for c in res["cases"]:
        for x in c["agreement"]["candidate_disagreements"]:
            L.append(f"- {c['case_id']} {x['candidate']}: {' vs '.join(x['judgments'])} — {'adjudicated' if x['adjudicated'] else 'UNRESOLVED'}")
        for x in c["agreement"]["finding_disagreements"]:
            ref = x["finding"]["check"] + ":" + (x["finding"].get("rule") or x["finding"].get("requirement") or x["finding"].get("candidate") or "")
            L.append(f"- {c['case_id']} finding {ref}: {' vs '.join(x['judgments'])} — {'adjudicated' if x['adjudicated'] else 'UNRESOLVED'}")
    L.append("")

    # workflow
    L += ["## 7. Workflow value (only where measured or observed)", "", "| Metric | Value |", "|---|---|",
          f"| W1 Cases with measured review time | {_r(wf['W1_cases_with_measured_time'])} |",
          f"| W1 Review minutes, baseline vs. assisted (measured cases only) | "
          + (f"{wf['W1_baseline_minutes']} vs. {wf['W1_assisted_minutes']}" if wf["W1_baseline_minutes"] is not None else "not measured") + " |",
          "| W2 Additional relevant candidates per requisition | "
          + (", ".join(f"{k}: {v}" for k, v in wf["W2_additional_relevant_per_requisition"].items()) or "no case with a baseline") + " |",
          f"| W3 Review burden (irrelevant surfaced + irrelevant via corrections + rejected findings) | {wf['W3_review_burden']} |",
          f"| W4 Recruiter decisions changed after inspecting evidence | {_r(wf['W4_decisions_changed_after_evidence'])} |",
          f"| W5 Downstream outcomes observed / attributable / not observed | {wf['W5_downstream_observed']} / {wf['W5_downstream_attributable']} / {wf['W5_downstream_not_observed']} |", "",
          "Recruiter decisions and downstream outcomes are reported separately from independent review. No downstream "
          "outcome is attributed to Screening Assurance unless the partner's records mark it attributable, and none implies causation.", ""]

    # by scenario
    L += ["## 8. By scenario", "", "| Scenario | Cases | Resolved labels | Interpretable | Relevant surfaced | Relevant missed | Irrelevant surfaced | Baseline missed relevant | Recovered | Findings confirmed | Violations |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in res["by_scenario"]:
        L.append(f"| {s['scenario']} | {', '.join(s['cases'])} | {s['resolved_labels']} | {'yes' if s['interpretable'] else 'no — sample too small'} | "
                 f"{s['relevant_surfaced']} | {s['relevant_missed']} | {s['irrelevant_surfaced']} | {s['baseline_missed_relevant']} | "
                 f"{s['recovered_by_product']} | {s['findings_confirmed']} | {s['violations']} |")
    L.append("")

    # versions per case
    L += ["## 9. Versions and inputs per case", "", "| Case | Requisition | Policy | Decisions snapshot | Product run sha256 | Inputs |", "|---|---|---|---|---|---|"]
    for c in res["cases"]:
        inputs = ", ".join(f"{k} `{v[:10]}`" for k, v in sorted(c["inputs_sha256"].items()))
        L.append(f"| {c['case_id']} | {c['requisition_id']} | {c['policy_version']} | {c['decisions_snapshot']} | "
                 f"`{c['product_run']['result_sha256'][:12]}` | {inputs} |")
    L.append("")

    # limitations
    L += ["## 10. Limitations, sample size and unresolved items", ""]
    L += [f"- {x}" for x in res["limitations"]]
    unresolved = [f"{c['case_id']}:{x} ({c['labels'][x]})" for c in res["cases"] for x in c["unresolved_candidates"]]
    L += [f"- Unresolved or unknown candidates: {_ids(unresolved)}", ""]

    L += ["## Metric definitions", "", "| ID | Metric | Numerator | Denominator | Eligibility | Unknown handling | Minimum evidence |",
          "|---|---|---|---|---|---|---|"]
    for d in res["definitions"]:
        L.append(f"| {d['id']} | {d['name']} | {d['numerator']} | {d['denominator']} | {d['eligibility']} | {d['unknown_handling']} | {d['minimum_evidence']} |")
    L.append("")
    return "\n".join(L)


def render_validation_compare_markdown(cmp: dict[str, Any]) -> str:
    a, b = cmp["a"], cmp["b"]
    L = ["# Validation comparison", "", f"> **{cmp['label']}**", "",
         "| | A | B |", "|---|---|---|",
         f"| Result | `{a['result_id']}` | `{b['result_id']}` |",
         f"| Engine | {a['engine_version']} | {b['engine_version']} |",
         f"| Knowledge | `{a['knowledge']}` | `{b['knowledge']}` |",
         f"| Dataset | {a['dataset']['id']} v{a['dataset']['version']} | {b['dataset']['id']} v{b['dataset']['version']} |", ""]
    L += [f"> Warning: {w}" for w in cmp["warnings"]]
    L += ["", "## Regressions", ""]
    L += [f"- {r}" for r in cmp["regressions"]] or ["- none"]
    L += ["", "## Metric changes", "", "| Metric | A | B |", "|---|---|---|"]
    L += [f"| {k} | {v['a']} | {v['b']} |" for k, v in cmp["metric_deltas"].items()] or ["| (no changes) | | |"]
    L += ["", "## Product group changes", "", "| Case | Candidate | A | B | Independent label |", "|---|---|---|---|---|"]
    L += [f"| {g['case']} | {g['candidate']} | {g['a']} | {g['b']} | {g['label']} |" for g in cmp["group_changes"]] or ["| (none) | | | | |"]
    L.append("")
    return "\n".join(L)
