# Pilot measurement plan

The pilot must establish two things before the product is scaled:

1. **Are the additional candidates genuinely qualified?** (not just "more candidates")
2. **Is the recruiter effort justified?** (incremental qualified candidates per unit of recruiter effort)

Acceptance criteria are fixed *before* the pilot starts and recorded in the engagement agreement.

## Scope

- One design partner, one job family, 5–10 requisitions with recurring volume.
- Inputs: requisition exports with screening configuration (ATS export preferred over recruiter
  documentation — the report discloses which), authorized de-identified candidate evidence, employer policy.
- A named experienced recruiter and hiring manager who validate findings.

## Phases and instruments

| Phase | Activity | Instrument in this repo |
|---|---|---|
| 0. Baseline | Record the baseline period for each requisition *before* any change. | `outcomes.yaml` → `baseline` |
| 1. Diagnose | Run the engine; deliver reports. | `sa diagnose`, `report.html` |
| 2. Independent validation | A recruiting expert who did not see the engine's output labels a sample of excluded candidates (meets / does not meet / insufficient evidence). These become eval cases. | `evals/cases/*.yaml` (`expert_labels`) |
| 3. Review | Recruiter and hiring manager decide each finding with a rationale. | `decisions.yaml` |
| 4. Correct | Employer implements accepted changes in the ATS. | `changes.yaml` |
| 5. Observe | Record after-change period and every additional candidate review (minutes, outcome, stage reached). | `outcomes.yaml` → `after_change`, `candidate_reviews` |
| 6. Report | Measured results, separately labelled estimates, attribution, new risks. | report §8, `sa portfolio` |

Blind labelling in phase 2 matters: labels made after seeing the engine's evidence are anchored by it.

## Metrics

### Diagnostic quality

| Metric | Definition | Pilot target (proposed) |
|---|---|---|
| Finding confirmation rate | Findings an independent expert agrees are real ÷ findings reviewed | ≥ 80% for Level 1, ≥ 60% for Level 2 |
| Actionability | Findings that led to accept / reclassify / confirm-necessary (not "ignore") ÷ findings | ≥ 60% |
| Accept vs. reject, with reasons | From `decisions.yaml` | Reported; reasons coded into themes |
| Recurrence | Same check type across requisitions | Reported (`sa portfolio`) |

### Candidate quality and effort

| Metric | Definition | Pilot target (proposed) |
|---|---|---|
| Additional candidates receiving meaningful review | `candidate_reviews` count | Reported |
| Surfacing precision | Confirmed meets requirements ÷ additionally reviewed | ≥ 0.6 |
| False-positive rate | Confirmed does-not-meet ÷ additionally reviewed | ≤ 0.3 |
| Incremental qualified candidates per recruiter hour | Confirmed meets ÷ (review minutes ÷ 60) | ≥ 1.0 |
| Change in recruiter hours per qualified candidate | after − baseline | Not worse |
| Time to qualified shortlist | after − baseline (days) | Reported |
| Guardrail violations | Anyone surfaced who lacks a protected requirement | **0** (hard stop) |

### Commercial

- Time to complete the assurance review per requisition.
- Customer willingness to pay and to reuse the process on the next requisitions.

## Attribution rules

- Every outcome file must state its `comparison_method`. Pre/post on the same requisition is the minimum;
  matched comparison requisitions in the same job family, unchanged, are better.
- **Measured** values (recorded reviews, period counts) and **estimated** values (avoided sourcing cycles,
  cost) are never summed or shown together. Estimates require explicit `estimation_assumptions` with a source.
- An improvement is *associated with* approved corrections unless the comparison controls for other factors.
- Report new risks observed (e.g. extra review volume from broader matching) alongside gains.

## Decision at the end of the pilot

Continue to Phase 3 (repeatable product) only if: guardrail violations are zero; Level 1 confirmation rate and
surfacing precision meet targets; incremental qualified candidates per recruiter hour is at least the baseline
yield; and the partner chooses to reuse the process. Otherwise, use the coded rejection reasons to decide
whether the problem is knowledge (fix and re-evaluate), checks (adjust), or market (stop).
