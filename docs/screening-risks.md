# Forward screening assurance (screening risks)

The workbench looks at one requisition from both sides:

- **Look back — Candidate discovery:** who in the authorized pool and applicant set has evidence that supports review.
- **Look forward — Screening risks:** where the supplied screening rules may exclude people whose evidence could meet
  the requirement, what a proposed correction would change, and what must stay blocking.

The deterministic engine and the versioned knowledge pack stay authoritative. Corrections are **simulated, never
applied** to the requisition, the knowledge pack or any ATS. Nothing here calls a candidate qualified.

## Audit of the landed slices (what was reused, what was missing)

| Already in place | Reused for screening risks |
|---|---|
| Design checks over rules and requirements, each with a correction *patch* (`engine/checks.py`) | Source of rule-level risks and the proposed corrections |
| Deterministic rule simulation (`engine/rules.py: evaluate_rule, apply_patches`) | Before/after comparison per correction |
| Requirement evidence with equivalency conditions, skill combinations and the protected-requirement guardrail (`engine/candidates.py: requirement_evidence`) | Relevance, mandatory and insufficient-evidence categories |
| Combined-correction candidate assessment and candidate-review opportunities | "Newly eligible together with the other proposed corrections"; per-candidate before/after |
| Pool contract, authorization, expiry and freshness rules | Which pool records may enter a simulation (now shared in `engine/pool.py`) |
| Workspace: immutable hashed inputs, run snapshots, decision carry-over, exports, retention, audit, verification | Unchanged lifecycle; the new outputs live inside `result.json` |

Missing, and added in the smallest form:

1. A per-finding **before/after simulation** with explicit impact categories, over applicants *and* authorized pool records (`engine/risks.py`).
2. A finding for **protected requirements** (`mandatory_requirement_protected`) instead of only listing them as suppressed.
3. Per-candidate detail for **exclusions whose cause cannot be established** (which rules could not be evaluated).
4. A mapping of existing checks onto the six **screening-risk categories**.
5. **Decision history** (`decision-history.jsonl`) and carry-over that reports decisions made under different knowledge, inputs or finding content.
6. Export (`screening-risks.yaml`, `decision-history.jsonl`), evaluation and UI wiring.

No second evidence engine, decision contract or persistence layer was introduced.

## Screening-risk categories

| Category | Engine checks |
|---|---|
| Preferred criterion enforced as a knockout | `preferred_enforced_as_knockout` |
| Rule narrower than the requirement | `rule_narrower_than_requirement`, `threshold_inconsistency`, `experience_path_narrower`, `credential_stricter_than_requirement`, `unstated_requirement_enforced` |
| Terminology not recognized | `literal_term_missing_variants` |
| Potentially equivalent experience | `equivalent_path_blocked`, `alternatives_not_considered` (equivalencies from the knowledge pack only, subject to employer policy) |
| Mandatory requirement protected | `mandatory_requirement_protected` — no correction is ever proposed |
| Insufficient evidence or unknown cause | `unexplained_exclusions`, `unverified_necessity` |

Candidate-review opportunities get the most specific category their evidence supports: an equivalency or combination
path → *potentially equivalent experience*; unlocked by a terminology correction alone → *terminology*; a preferred
knockout among the causes → *preferred criterion*; otherwise *rule narrower*.

## Correction simulation

For each finding with a proposed correction, the supplied rule and the corrected rule are both evaluated against:

- every applicant in `candidates.yaml`, and
- every **authorized, unexpired, fresh** record in `candidate-pool.yaml` (blocked records never enter a simulation).
  Pool results are **hypothetical** — those people did not apply — and are labelled that way everywhere.

| Category | Meaning |
|---|---|
| Excluded by the supplied rule | Fails the rule as supplied |
| Would pass the proposed rule | Fails as supplied, passes as corrected |
| Still fail a mandatory requirement | Would pass, but a protected requirement is not met in a complete record |
| Evidence insufficient to tell | The rule cannot be evaluated (e.g. no knockout answer recorded; pool records have none), or a mandatory requirement cannot be verified, or the record is partial |
| Pass the rule, but relevance not established | Would pass, but required evidence is missing — this is where irrelevant matches end up |
| Relevant evidence, but still fail other supplied rules | Would pass and evidence is relevant, yet other rules still exclude or cannot be evaluated |
| Newly eligible for human review | Would pass, evidence covers the requirements, and either every other supplied rule passes, or the same combined simulation used for candidate-review opportunities clears them |

Findings without a correction (classification questions, unknown causes, no candidate evidence) say so and are not
simulated; a requisition reviewed before publication produces **rule-level risks**, not candidate claims.

Candidate-review opportunities additionally show the candidate's own rule-by-rule before/after.

## Evidence limits

- Rules supplied as an ATS configuration **export** are described as such — never as a live ATS audit. Recruiter
  documentation is labelled as documentation.
- An exclusion is "established" only for applicants and only by the supplied rules; a missing knockout answer
  makes the outcome unknown, not a false negative.
- Newly eligible means *eligible for human review*. It is never a qualification decision and never a confirmed
  false negative; proving one needs outcome evidence (`outcomes.yaml`) from a design partner.
- Equivalencies come only from the versioned knowledge pack and are subject to employer policy rejections. There is
  no semantic-similarity matching and no language model in the decision path.
- Simulations store candidate ids, rule outcomes and requirement ids — not evidence text — so the risk export does
  not copy candidate evidence.

## Decisions, history and reproducibility

- Decisions use the existing vocabulary and contract (accept, reject, defer, request evidence, confirm necessary,
  reclassify as preferred), each with a required rationale and reviewer.
- Every decision is appended to `decision-history.jsonl` with the run, knowledge fingerprint, input fingerprint and a
  hash of the finding as the reviewer saw it. `decisions.yaml` keeps the current decision.
- On the next run, decisions are reported as applied, stale (finding gone) or **made in a different context**
  (knowledge, inputs or the finding changed) so a reviewer can look again.
- Simulations are part of `result.json`, so run snapshots, exports and byte-for-byte verification cover them.
  Verification also checks the engine version.
- Retention deletes candidate-level data, including candidate entries in the decision history.

## Demonstration

1. `sa workbench`, enter a reviewer name, load `REQ-SRE-0142`, run.
2. Open **Screening risks**. Choose *Rule narrower than the requirement*, then *Q1 is narrower than R1*.
3. Read the evidence (requirement R1 versus rule Q1), then the **correction simulation**: 13 records excluded,
   C-103, C-106 and C-110 newly eligible (together with other proposed corrections), C-104 and the pool's P-204 in
   *relevance not established*, P-202 and P-203 hypothetical pool records that still fail other rules. Open *Why each
   candidate is in these categories*; candidate ids link to their discovery evidence.
4. Record **Accept** with a rationale; the decision history shows who decided what in which run.
5. Filter *Mandatory requirement protected* on `REQ-LH-0217` to see a protected licence with no correction proposed.
6. **Review and export** → re-run → export *Screening risks and simulations*; **Verify** the run.

`sa eval` reports the synthetic screening-risk metrics (relevant surfaced/missed, irrelevant surfaced,
mandatory-requirement and policy violations, results needing human verification, expectations met), and
`sa eval-compare` gates knowledge changes on them.
