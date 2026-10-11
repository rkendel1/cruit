# Design-partner validation and outcome measurement

This guide covers how to measure Screening Assurance against hiring cases that people have reviewed
independently: what the repository already measured, the dataset contract, how to run a measurement,
what each metric means and what the results cannot show.

> The only dataset in this repository, `evals/validation/northwind-synthetic.yaml`, is **synthetic**.
> Its labels were written alongside the fixtures. Its results show that the measurement loop works.
> They are **not** design-partner evidence and they say nothing about real-world effectiveness. Every
> result and report built from it carries that label.

## 1. Audit: what already existed and what was missing

| Existing instrument | What it measures | Gap for design-partner validation |
|---|---|---|
| `docs/pilot-measurement-plan.md` | Pilot phases, proposed targets, attribution rules | Phase 2 ("independent validation") had no data contract. Labels were meant to become eval cases, which mixed partner data into the regression suite. |
| `screening_assurance.measure` (`outcomes.yaml`) | Outcomes per requisition: baseline vs. after-change periods and recruiter reviews of added candidates. Measured and estimated values are kept apart. | No independent relevance label, no reviewer disagreement and no comparison of findings against reviews. |
| `sa eval` / `sa eval-compare` | Regression gate for knowledge changes, run on authored labels (one label per candidate), with discovery and screening-risk expectations | One label per candidate means no disagreement, no adjudication and no "unknown". Records no baseline (what the ATS actually did). Results are always synthetic. |
| Workbench runs, decision history, exports, retention | What a recruiter decided in the product, with snapshots and retention | Recruiter decisions are made after seeing the product's output, so they are not independent review. |
| De-identification checks (`contracts.py`) | Prohibited fields and contact details in candidate evidence | Did not cover review data. |

These pieces were **missing**:

- a versioned contract for reviewed cases
- a baseline view kept apart from the product view
- resolution of reviewer disagreement that keeps the disagreement visible
- metrics with explicit numerators, denominators and handling of unknowns
- violation reporting that no other metric can hide
- results that are versioned and never overwritten

**What was added.** All of it extends the existing code. There is no new engine, eval framework or database.

- `schemas/validation_dataset.schema.json`: the dataset contract (`sa schema validation_dataset`).
- `measure/validation.py`: loads and checks a dataset, re-runs the existing `diagnose` and `discover` on the
  dataset's inputs, and computes the metrics below. The old `measure.py` became the `measure` package; its API
  is unchanged.
- `report/validation.py`: a Markdown report, written next to a machine-readable `result.json`.
- `sa measure`, `sa measure-compare` and `sa check validation_dataset`.

`sa eval` and `sa eval-compare` are unchanged and remain the knowledge regression gate.

## 2. Preparing a dataset

A dataset is one YAML file. It references the existing input contracts (requisition, policy,
candidates, candidate pool and, optionally, decisions) by paths relative to itself. Each of those files
is validated by its own contract, including the existing checks for protected characteristics and
contact details.

```yaml
dataset_id: acme-sre-2026q4          # opaque
contract_version: 1
kind: design_partner                 # or synthetic; synthetic is never reported as partner evidence
source: { provider: Acme, dataset_version: "3", collected_at: "2026-11-01", description: ... }
authorization:
  basis: DPA section 4
  de_identified: true                # required; must be true
  permitted_uses: [product_validation]
  retention_days: 180                # measurement refuses to run once expired; stored results are purged
  deletion: delete_results_only
  granted_by: privacy office
cases:
  - case_id: SRE-1
    scenario: software-infrastructure   # grouping for the per-scenario breakdown
    requisition: inputs/req.yaml
    policy: inputs/policy.yaml
    candidates: inputs/candidates.yaml
    pool: inputs/pool.yaml              # must permit product_validation or rediscovery_review
    baseline:                           # what the existing process actually did
      source: ats_export                # ats_export | recruiter_records | not_available
      observations:
        - { candidate: C-1, outcome: rejected, excluded_by_rule: Q1, basis: observed }
        - { candidate: P-9, outcome: not_applied, basis: observed }
        - { candidate: C-7, outcome: unknown, basis: unknown }
    candidate_assessments:              # independent human review against the actual requirements
      - candidate: C-1
        reviews:
          - { reviewer: REV-A, judgment: relevant, mandatory: met, rationale: "...", reviewed_at: "2026-11-02", saw_product_output: false }
          - { reviewer: REV-B, judgment: not_relevant, mandatory: met, rationale: "...", reviewed_at: "2026-11-03", saw_product_output: false }
        adjudication: { judgment: relevant, adjudicator: ADJ-1, rationale: "...", decided_at: "2026-11-04" }
    finding_reviews:                    # independent review of screening-risk findings
      - finding: { check: rule_narrower_than_requirement, rule: Q1 }
        reviews: [{ reviewer: REV-A, judgment: confirmed, rationale: "...", reviewed_at: "2026-11-02" }]
    recruiter_decisions: [...]          # optional; kept apart from independent review
    downstream: [...]                   # optional; observed outcomes only, with an `attributable` flag
    workflow_time: { measured: true, baseline_minutes: 90, assisted_minutes: 55, method: stopwatch }
```

Rules the loader enforces. A dataset that breaks any of them is rejected, and every problem is listed:

- **Opaque references only.** Case, candidate and reviewer references must match `[A-Za-z0-9._-]{1,40}`.
  Free text containing an email address or phone number is rejected. Unknown fields are rejected, so a
  `name` or `gender` field cannot be added.
- **Authorization.** `de_identified: true`, `product_validation` among the permitted uses, an unexpired
  retention period, and pools authorized for validation or rediscovery.
- **Referential integrity.** Every candidate reference must exist in the case's inputs. Case IDs,
  per-candidate entries, finding reviews and reviewers within one item must not repeat. Candidates and
  requisition must match. A `not_available` baseline must carry no observations.
- **Explicit unknowns.** Use `unassessable` when the evidence cannot support a judgment, `cannot_verify`
  for a mandatory requirement that cannot be checked, and `unknown` or `not_applied` for baselines. Leave a
  candidate out of `candidate_assessments` only when nobody reviewed them. The candidate is then reported
  as **unreviewed**, never as a negative.
- **Blind review.** Set `saw_product_output: false` only if the reviewer judged the case without seeing
  Screening Assurance output. The report counts blind reviews.

Check a dataset without measuring it: `sa check validation_dataset path/to/dataset.yaml`.

## 3. Running a measurement

```bash
sa measure evals/validation/northwind-synthetic.yaml                 # working knowledge pack
sa measure dataset.yaml --knowledge env:production --out validation-results
sa measure-compare validation-results/<ds>/<id-a>/result.json validation-results/<ds>/<id-b>/result.json
```

- Each result is written to `<out>/<dataset_id>/<result_id>/` as `result.json` and `report.md`.
  `result_id` is derived from four things: the hash of the dataset and every input file, the engine
  version, the knowledge fingerprint and the evaluation-contract version. So:
  - Changed inputs or knowledge produce a **new** result next to the earlier one, which is kept.
  - Re-running unchanged inputs reproduces the same result (`Reproduced existing …`).
  - If a stored result with the same id has different content, `sa measure` **refuses to overwrite it**.
    That happens when the code changed without a version bump, and it needs investigating.
- `sa measure` exits with status 1 when any mandatory or policy violation occurred, so it can gate CI.
- `sa measure-compare` lists metric deltas and per-candidate group changes across engine or knowledge
  versions, and warns if the two results used different datasets. It exits with status 1 on these
  regressions: more violations, more irrelevant candidates surfaced, more irrelevant candidates surfaced
  by corrections, or more relevant candidates missed.
- Results contain no candidate evidence text and no reviewer rationale, only opaque references, labels,
  groups, counts and hashes. Nothing is sent anywhere. Expired results are deleted at the start of every
  `sa measure` run that uses the same output directory.
- `validation-results/` is git-ignored. Keep partner datasets and results out of the repository.

## 4. Interpreting the metrics

Every metric in `result.json` has an entry under `definitions`, which gives its numerator, denominator,
eligibility, handling of unknowns and minimum evidence. Each rate is reported as numerator, denominator
and rate. There is **no single aggregate score**.

**Label resolution.** Each candidate's reviews are resolved as follows:

- One review: that review's judgment.
- Several reviews that agree: the shared judgment.
- Reviews that disagree, with an adjudication: the adjudicated value. The disagreement is still reported.
- Reviews that disagree, without an adjudication: **unresolved**.

Unresolved, unassessable and unreviewed candidates are excluded from the relevance rates and listed by
name.

| Group | What it answers | Read it with |
|---|---|---|
| Coverage (§1) | How much of the population has a resolved label, which cases lack a baseline, how many findings went unreviewed | Low coverage makes every rate below less meaningful |
| Baseline vs. product (§2, B1–B3) | Which relevant candidates the existing process excluded (observed only), and how many of those the product surfaced | B1 counts *inferred* baseline outcomes separately. Pool records that never applied have no baseline. |
| Discovery (D1–D5) | Relevant candidates surfaced or missed, irrelevant candidates surfaced, surfaced candidates of unknown relevance, results that need verification | Blocked or active-workflow candidates are not misses. They are counted separately. |
| Screening risks (F1–F9) | Findings confirmed, rejected, deferred, unresolved or unreviewed; corrections that reveal relevant or irrelevant candidates; exclusions with an unknown cause; findings without a verified baseline | An unreviewed finding is never counted as confirmed. A finding may describe a real rule-level risk even when no exclusion was observed (F9). |
| Violations (V1, V2) | Surfaced or newly eligible candidates whose mandatory requirement reviewers judged not met; simulations that make a candidate eligible while failing a protected requirement; corrections to protected rules; blocked records surfaced; equivalencies the policy rejects | Each violation is listed individually, and the report states explicitly whether any occurred. `cannot_verify` is listed separately and counts as neither a violation nor a pass. |
| Agreement (§6) | Reviewer agreement and disagreement, adjudications, blind reviews | Unresolved disagreements stay visible |
| Workflow (W1–W5) | Review time (measured cases only), additional relevant candidates per requisition, review burden, recruiter decisions changed after seeing evidence, downstream outcomes | Nothing is imputed. Recruiter decisions and downstream outcomes are reported apart from independent review. A downstream outcome counts as attributable only when the partner's records say so. |
| By scenario (§8) | The same counts per scenario | Scenarios with fewer than 10 resolved labels are marked *not interpretable* |

## 5. Limitations

- **Synthetic is not evidence.** Results from `kind: synthetic` show only that the pipeline computes what
  it claims to.
- **Correlation, not causation.** A relevant candidate the product surfaced after the baseline excluded
  them shows a gap the product can find. It does not show that hiring outcomes improved. Downstream
  outcomes are reported, not attributed, unless partner records establish attribution. Even then they are
  not causal estimates.
- **Small samples.** A few requisitions with tens of labelled candidates cannot support general accuracy
  claims. Rates come with their denominators, and small scenarios are flagged.
- **Reviewer anchoring.** Reviews made after seeing product output are anchored by it. The report counts
  blind reviews, and the partner should aim for blind relevance labels.
- **The product view is a re-run.** It is the deterministic engine applied to the dataset's inputs, not a
  record of what a recruiter saw on the day. Simulated corrections are hypothetical and are not changes to
  the employer's process.
- **Rules come from supplied exports or documentation**, not a live ATS audit.
- **No learning.** Labels, recruiter decisions and outcomes never change knowledge automatically. Knowledge
  changes still go through proposals, `sa eval` and release gates.
