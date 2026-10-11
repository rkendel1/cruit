# Candidate Rediscovery Workbench

A local-first recruiter workflow on top of the Screening Assurance engine. It answers, for one requisition:

> Why did this person appear, what evidence supports reviewing them, what remains unknown, and what do I want to do next?

The deterministic engine and the versioned knowledge pack stay authoritative. The workbench is a thin
presentation and interaction layer: Python orchestrates the engine (`workbench/workspace.py`), a
standard-library HTTP server exposes it on loopback (`workbench/server.py`), and a single static page
renders results (`workbench/static/`). The browser code contains no matching, grouping, scoring or
knowledge interpretation — it displays what the engine returned and posts explicit decisions.

```bash
sa workbench [--port 8765] [--workspace ./workspace] [--no-browser]
```

## The four views

| View | What it shows | Engine source |
|---|---|---|
| Requisition intake | Example or uploaded package; per-file validation; input fingerprints; supplied ATS configuration export vs recruiter documentation vs missing (never described as a live audit); pool permitted uses, age limit and retention; requirements, rules and policy; knowledge revision and engine version | `contracts`, `Workspace.input_summary` |
| Candidate discovery | Evidence groups, per-candidate evidence ledger, unknowns, mandatory-requirement issues, supplied-rule exclusions, freshness, constraints, run and knowledge reference, decision form | `engine/discovery.py` |
| Screening risks | Screening-risk findings (see [screening-risks.md](screening-risks.md)) with before/after correction simulations; Level 1–3 with the requirement and rule, evidence, affected candidates, confidence, proposed action and trade-off, knowledge reference, decision form with the dispositions the decision model allows for that finding | `engine/checks.py`, `engine/candidates.py`, `measure.py` |
| Review and export | Pending work, decisions recorded after the run (re-run to apply), carried-over and stale decisions, exports, measured outcomes vs estimates, run history with reproducibility verification, knowledge evaluation and comparison | `Workspace.run/verify_run/export/evaluate/compare` |

## Discovery: from "affected by rules" to "supported by evidence"

The MVP engine only assessed applicants affected by supplied screening rules. Rediscovery needs candidates
from earlier requisitions and records with no known exclusion, so this slice adds one explicit contract —
[`candidate_pool`](../src/screening_assurance/schemas/candidate_pool.schema.json) — and one engine function,
`discover()`, which reuses the existing requirement-evidence logic (same knowledge, same equivalency
conditions, same protected-requirement guardrail).

Groups (no ranking, no score; order within a group is by id):

| Group | Rule |
|---|---|
| Direct evidence | Every required requirement evidenced without an alternative path |
| Potentially transferable | Every required requirement covered; at least one via an equivalency or skill combination that a recruiter must verify |
| Insufficient evidence | Some required evidence exists, but the record is declared partial, or a mandatory credential cannot be verified because credentials were not supplied |
| Not surfaced | A mandatory requirement is not met, or required evidence is missing from a record declared complete. Records with no evidence for any required requirement are **counted, not listed** |
| Not available for action | Not authorized for `rediscovery_review`, authorization expired, or evidence older than `max_evidence_age_days`. **No evidence is shown** and no decision can be recorded |
| Already in active review | ATS status `in_review` / `advanced`; not repeated |

For current applicants, "excluded by a supplied rule" comes from the existing rule simulation and is labelled
*established* only when the configuration was exported or read from the ATS; recruiter-documented rules are
labelled indicative. For pool records, the workbench says plainly that no supplied rule applies and that a
prior disposition is not explained by any supplied rule.

`evidence_coverage` is how the engine tells *absence* from *unknown*: a missing license in a **complete**
credential list means the mandatory requirement is not met; in a list that was **not supplied** it means the
requirement cannot be verified, so the record can only appear as *Insufficient evidence*.

## Data boundaries

- File-based only. Supported inputs: `requisition`, `policy`, `candidates` (current applicants),
  `candidate_pool`, `outcomes` — YAML or JSON, at most 2 MB each, validated against their JSON Schemas.
  Contracts cap list sizes and string lengths.
- No names, email addresses, phone numbers, photos or protected characteristics: unknown fields are
  rejected, named personal fields get an explicit error, and free-text evidence containing an email address
  or phone number is rejected.
- Source records are referenced by opaque `source_record_ref`; the mapping to real identities stays with the
  employer and never appears in outputs.
- The workbench never infers consent. `contact_status` is shown only when supplied; otherwise the record says
  contact permission is not established. A prior application is context, not permission.
- No ATS connector, ATS writes, outreach, language-model extraction or autonomous decisions.

## Local working area

```
workspace/
  audit.jsonl                         session creation and deletion events
  sessions/<S-…>/
    session.json                      inputs (sha256), retention deadline, deletion behaviour
    inputs/                           validated copies; any later modification is detected and blocks runs
    decisions.yaml                    finding decisions (existing `decisions` contract)
    review-decisions.yaml             candidate decisions (`review_decisions` contract)
    audit.jsonl                       runs, decisions, exports, verifications — ids and hashes only, never evidence or rationale text
    runs/<R-…>/
      run.json                        input hashes, knowledge fingerprint and spec, engine version, output hashes, carried-over decisions
      knowledge/                      copy of the exact knowledge documents used
      decisions.yaml, review-decisions.yaml   decisions as applied to this run
      result.json, discovery.json
```

**Retention.** A session's candidate data is deleted after the shortest `retention_days` among its candidate
inputs, counted from import. With `deletion: delete_candidate_data` the candidate inputs, runs and candidate
decisions are removed and the session is marked; with `delete_workspace_session` the whole session is removed.
Retention is applied on start-up and on every API request. Reviewers can delete a session at any time.

**Reproducibility.** *Verify* re-computes a run from its stored input fingerprints, knowledge snapshot and
decision snapshot, and compares the result and discovery hashes. Editing the working knowledge pack does not
affect earlier runs. Tampering with stored inputs makes verification fail and blocks new runs.

**Decisions across runs.** Finding decisions are keyed by the engine's stable finding ids; candidate decisions
by opaque candidate id. A decision whose finding or candidate no longer appears is kept and reported as stale,
not silently applied or deleted. Finding decisions take effect on the next run (rejecting a finding withdraws
its simulated correction; reclassifying an unverified requirement changes how it is treated).

## Security model

- Binds to `127.0.0.1` by default and refuses non-loopback addresses.
- Every API request must carry a per-launch random token (`X-SA-Token`), delivered only inside the served page;
  cross-site pages cannot read it. The `Host` header must be a loopback name (DNS-rebinding defence).
- JSON request bodies only, with a size limit checked before the body is read.
- `Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self' …`, `X-Frame-Options: DENY`,
  `no-store` caching. The UI builds DOM with `textContent`; it never injects data as HTML.
- Request logs contain method, path and status only. Error responses never echo request bodies.
- CSV exports neutralize spreadsheet formulas.

## Exports

Per run: candidate review list (CSV, YAML), Markdown and HTML report (screening findings plus a rediscovery
section, with a provenance header), findings and discovery JSON, finding and candidate decisions, accepted
configuration changes, and a ZIP bundle with a hash manifest and the knowledge snapshot. Exports reflect the
selected run; decision files reflect everything recorded so far.

## Evaluation

Discovery is evaluated on labelled **synthetic** fixtures in `evals/discovery/`, as part of `sa eval` and
`sa eval-compare` (and from the workbench's *Knowledge and evaluation* panel). Reported: relevant surfaced,
relevant missed, irrelevant surfaced, over-claimed certainty, mandatory-requirement violations, blocked-record
violations, results needing human verification, and recruiter dispositions/time (not measured in fixtures;
recorded in the workspace in real use). These are not real-world accuracy figures.
