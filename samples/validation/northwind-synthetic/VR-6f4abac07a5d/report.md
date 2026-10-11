# Validation result `VR-6f4abac07a5d` — northwind-synthetic

> **SYNTHETIC DATASET — results demonstrate the measurement loop, not real-world effectiveness**

| Provenance | |
|---|---|
| Dataset | `northwind-synthetic` v1 (synthetic), contract v1, provider Screening Assurance test fixtures, collected 2026-10-10 |
| Dataset inputs sha256 | `714fe06f34ae0d77…` |
| Engine | 0.2.0 |
| Knowledge | `core@1.1.0+8a94e741e4` |
| Evaluation contract | validation-1 |
| Retention | delete after 2027-10-10 (delete results only) |

## 1. Dataset coverage and missing labels

3 case(s), 38 candidate record(s), 38 screening-risk finding(s).

| Relevance label (independent review) | Candidates |
|---|---|
| Relevant | 18 |
| Not relevant | 9 |
| Unassessable from supplied evidence | 4 |
| Reviewers disagree, not adjudicated (unresolved) | 1 |
| Not reviewed | 6 |

- Cases without a baseline: CSM-0388
- Screening-risk findings not reviewed: 29
- Unknown, unresolved and unreviewed labels are never counted as relevant or irrelevant.

## 2. Existing process vs. Screening Assurance (side by side)

The baseline column is what the existing screening process did, as recorded by the partner. The Screening Assurance column is a deterministic re-run of the product on the same inputs. Simulated corrections are not changes to the employer's process.

### SRE-0142 · REQ-SRE-0142 · software-infrastructure

Baseline source: ats export. As of 2026-10-10. Policy 2026.2. Rules Q1, Q2, Q3, Q4, Q5, Q6, Q7 (ats export verified).

| Candidate | Baseline outcome (basis) | Screening Assurance group | Independent label |
|---|---|---|---|
| C-101 | advanced (observed) | active workflow | relevant |
| C-102 | rejected (observed), rule Q1 | direct | relevant |
| C-103 | rejected (observed), rule Q3 | transferable | relevant |
| C-104 | rejected (observed), rule Q4 | not surfaced | not relevant |
| C-105 | rejected (observed), rule Q3 | not surfaced | not relevant |
| C-106 | rejected (observed), rule Q1 | transferable | relevant |
| C-107 | rejected (observed), rule Q2 | not surfaced | unresolved |
| C-108 | rejected (observed), rule Q4 | direct | relevant |
| C-109 | rejected (observed), rule Q2 | direct | relevant |
| C-110 | rejected (observed), rule Q7 | direct | relevant |
| C-111 | rejected (observed) | not surfaced | not relevant |
| C-112 | rejected (observed) | not surfaced | unreviewed |
| C-113 | unknown (unknown) | direct | relevant |
| C-114 | rejected (inferred) | not surfaced | unassessable |
| P-201 | not applied (observed) | direct | relevant |
| P-202 | not applied (observed) | direct | relevant |
| P-203 | not applied (observed) | transferable | relevant |
| P-204 | not recorded | not surfaced | not relevant |
| P-205 | not recorded | insufficient | unassessable |
| P-206 | not recorded | blocked | relevant |
| P-207 | not recorded | blocked | unreviewed |
| P-208 | not applied (observed) | direct | relevant |
| P-209 | not recorded | blocked | unreviewed |

### LH-0217 · REQ-LH-0217 · transportation

Baseline source: recruiter records. As of 2026-10-10. Policy 2026.2. Rules Q1, Q2 (ats export verified).

| Candidate | Baseline outcome (basis) | Screening Assurance group | Independent label |
|---|---|---|---|
| C-301 | advanced (observed) | active workflow | relevant |
| C-302 | rejected (observed), rule Q1 | not surfaced | not relevant |
| C-303 | rejected (observed), rule Q2 | transferable | relevant |
| C-304 | rejected (observed) | not surfaced | not relevant |
| P-301 | not applied (observed) | direct | relevant |
| P-302 | not applied (observed) | not surfaced | not relevant |
| P-303 | not applied (observed) | insufficient | unassessable |

### CSM-0388 · REQ-CSM-0388 · customer-success

Baseline source: not available. As of 2026-10-10. Policy 2026.2. Rules Q1, Q2, Q3 (recruiter documentation).

| Candidate | Baseline outcome (basis) | Screening Assurance group | Independent label |
|---|---|---|---|
| C-201 | not available | active workflow | unreviewed |
| C-202 | not available | direct | relevant |
| C-203 | not available | not surfaced | not relevant |
| C-204 | not available | transferable | relevant |
| C-205 | not available | not surfaced | unreviewed |
| C-206 | not available | not surfaced | unreviewed |
| C-207 | not available | direct | unassessable |
| C-208 | not available | not surfaced | not relevant |

## 3. Discovery metrics

| Metric | Value |
|---|---|
| D1 Relevant candidates surfaced for human review | 15 / 15 (100%) |
| D2 Relevant candidates still missed | 0 / 15 (0%) |
| D3 Irrelevant candidates surfaced | 0 / 15 (0%) |
| D4 Surfaced, relevance not established | 3 / 18 (17%) |
| D5 Surfaced results requiring human verification | 7 / 18 (39%) |
| Relevant but blocked by authorization or evidence age (not a miss) | 1 |
| Already in active ATS review (excluded) | 3 |

| Baseline comparison | Value |
|---|---|
| B1 Relevant candidates the existing process excluded (observed) | 7 / 9 (78%) |
| B1 inferred only (not counted above) | 0 |
| B2 Of those, surfaced by Screening Assurance | 7 / 7 (100%) |
| B3 Of those, still missed by Screening Assurance | 0 / 7 (0%) |
| Pool records that never applied (no baseline applies) | 7 |
| Candidates with unknown baseline outcome | 14 |

| Case | Relevant surfaced | Relevant missed | Irrelevant surfaced | Relevance unknown | Unassessable |
|---|---|---|---|---|---|
| SRE-0142 | C-102, C-103, C-106, C-108, C-109, C-110, C-113, P-201, P-202, P-203, P-208 | none | none | P-205 | C-114, P-205 |
| LH-0217 | C-303, P-301 | none | none | P-303 | P-303 |
| CSM-0388 | C-202, C-204 | none | none | C-207 | C-207 |

## 4. Screening-risk metrics

Findings are matched to independent reviews by check and rule/requirement/candidate. Product findings are never their own ground truth: an unreviewed finding is not a confirmed finding.

| Metric | Value |
|---|---|
| F1 Findings independently confirmed | 6 / 38 (16%) |
| F2 Findings rejected (unsupported or irrelevant) | 1 / 38 (3%) |
| F3 Deferred or needing more evidence | 2 / 38 (5%) |
| F4 Reviewer disagreement, unresolved | 0 / 38 (0%) |
| F5 Not reviewed | 29 / 38 (76%) |
| F6 Corrections that reveal relevant candidates | 9 / 10 (90%) |
| F7 Corrections that surface irrelevant candidates | 0 / 10 (0%) |
| Newly eligible candidates with no resolved label | 1 |
| F8 Exclusion cause cannot be established (candidates + non-evaluable simulations) | 5 |
| F9 Findings without a verified baseline | 18 / 38 (47%) |
| Reviews for findings the product did not produce | 0 |

### SRE-0142 findings

| Finding | Check | Rule / requirement / candidate | Review | Baseline verified |
|---|---|---|---|---|
| `SA-REQ-SRE-0142-704c5892` | equivalent_path_blocked | Q1 / R1 | not reviewed | yes |
| `SA-REQ-SRE-0142-9164e1d0` | rule_narrower_than_requirement | Q1 / R1 | confirmed (agreed) | yes |
| `SA-REQ-SRE-0142-9403725f` | rule_narrower_than_requirement | Q2 / R1 | not reviewed | no |
| `SA-REQ-SRE-0142-d15dcf14` | threshold_inconsistency | Q2 / R1 | confirmed (adjudicated) | yes |
| `SA-REQ-SRE-0142-5302d6be` | equivalent_path_blocked | Q3 / R2 | not reviewed | yes |
| `SA-REQ-SRE-0142-3bc61a83` | preferred_enforced_as_knockout | Q4 / R5 | not reviewed | yes |
| `SA-REQ-SRE-0142-512cd6d3` | equivalent_path_blocked | Q4 / R5 | not reviewed | yes |
| `SA-REQ-SRE-0142-f01e2bd0` | rule_narrower_than_requirement | Q5 / R3 | not reviewed | yes |
| `SA-REQ-SRE-0142-48360a3a` | preferred_enforced_as_knockout | Q6 / R4 | not reviewed | yes |
| `SA-REQ-SRE-0142-99df8968` | unstated_requirement_enforced | Q7 | unsupported (single review) | yes |
| `SA-REQ-SRE-0142-b05a4c5a` | literal_term_missing_variants | Q1 | not reviewed | yes |
| `SA-REQ-SRE-0142-e3e3d885` | literal_term_missing_variants | Q2 | not reviewed | no |
| `SA-REQ-SRE-0142-a0ac83a9` | experience_path_narrower | Q2 / R1 | not reviewed | no |
| `SA-REQ-SRE-0142-9d626aeb` | literal_term_missing_variants | Q5 | not reviewed | no |
| `SA-REQ-SRE-0142-ff4b8adc` | unverified_necessity | R6 | needs more evidence (single review) | no |
| `SA-REQ-SRE-0142-5f56524c` | candidate_review_opportunity | C-102 | not reviewed | yes |
| `SA-REQ-SRE-0142-4989b969` | candidate_review_opportunity | C-103 | confirmed (single review) | yes |
| `SA-REQ-SRE-0142-36d39631` | candidate_review_opportunity | C-106 | not reviewed | yes |
| `SA-REQ-SRE-0142-cd635676` | candidate_review_opportunity | C-108 | not reviewed | yes |
| `SA-REQ-SRE-0142-c1d0ef0b` | candidate_review_opportunity | C-109 | not reviewed | yes |
| `SA-REQ-SRE-0142-82276566` | candidate_review_opportunity | C-110 | not reviewed | yes |
| `SA-REQ-SRE-0142-0b941a58` | unexplained_exclusions | — | not reviewed | no |

- Corrections reveal relevant: C-102, C-103, C-106, C-108, C-109, C-110; surface irrelevant: none; relevance unknown: none
- Exclusion cause unknown: C-113, C-114

### LH-0217 findings

| Finding | Check | Rule / requirement / candidate | Review | Baseline verified |
|---|---|---|---|---|
| `SA-REQ-LH-0217-31f7b18c` | mandatory_requirement_protected | Q1 / R1 | confirmed (single review) | yes |
| `SA-REQ-LH-0217-24c327f3` | literal_term_missing_variants | Q1 | not reviewed | yes |
| `SA-REQ-LH-0217-bdfae568` | literal_term_missing_variants | Q2 | not reviewed | no |
| `SA-REQ-LH-0217-b7263005` | experience_path_narrower | Q2 / R2 | confirmed (single review) | yes |
| `SA-REQ-LH-0217-6f063ac1` | candidate_review_opportunity | C-303 | not reviewed | yes |

- Corrections reveal relevant: C-303; surface irrelevant: none; relevance unknown: none
- Exclusion cause unknown: none

### CSM-0388 findings

| Finding | Check | Rule / requirement / candidate | Review | Baseline verified |
|---|---|---|---|---|
| `SA-REQ-CSM-0388-7da18d53` | equivalent_path_blocked | Q1 / R1 | confirmed (single review) | no |
| `SA-REQ-CSM-0388-7d038e7c` | credential_stricter_than_requirement | Q3 / R4 | not reviewed | no |
| `SA-REQ-CSM-0388-7f815e04` | preferred_enforced_as_knockout | Q3 / R4 | not reviewed | no |
| `SA-REQ-CSM-0388-1fa7cee2` | literal_term_missing_variants | Q1 | not reviewed | no |
| `SA-REQ-CSM-0388-095c74b9` | literal_term_missing_variants | Q2 | not reviewed | no |
| `SA-REQ-CSM-0388-309d1f67` | experience_path_narrower | Q2 / R1 | not reviewed | no |
| `SA-REQ-CSM-0388-16684b3b` | literal_term_missing_variants | Q3 | not reviewed | no |
| `SA-REQ-CSM-0388-a1beef17` | unverified_necessity | R4 | deferred (single review) | no |
| `SA-REQ-CSM-0388-7f33b017` | candidate_review_opportunity | C-202 | not reviewed | no |
| `SA-REQ-CSM-0388-dc08d1e4` | candidate_review_opportunity | C-204 | not reviewed | no |
| `SA-REQ-CSM-0388-ea6778d8` | candidate_review_opportunity | C-207 | not reviewed | no |

- Corrections reveal relevant: C-202, C-204; surface irrelevant: none; relevance unknown: C-207
- Exclusion cause unknown: none

## 5. Mandatory-requirement and policy violations

**No mandatory-requirement or policy violations occurred** in this dataset.


Mandatory requirements that reviewers could not verify, or disagreed on, for surfaced/newly eligible candidates (neither violation nor pass): SRE-0142: P-205, LH-0217: P-303

## 6. Reviewer agreement and adjudication

| | Candidates | Findings |
|---|---|---|
| Items with two or more reviews | 4 | 2 |
| Reviewers agreed | 2 | 1 |
| Reviewers disagreed | 2 | 1 |
| Disagreements adjudicated | 1 | 1 |

Candidate assessments made without seeing product output: 31.

- SRE-0142 C-104: not_relevant vs relevant — adjudicated
- SRE-0142 C-107: not_relevant vs relevant — UNRESOLVED
- SRE-0142 finding threshold_inconsistency:Q2: confirmed vs needs_more_evidence — adjudicated

## 7. Workflow value (only where measured or observed)

| Metric | Value |
|---|---|
| W1 Cases with measured review time | 1 / 3 (33%) |
| W1 Review minutes, baseline vs. assisted (measured cases only) | 95 vs. 60 |
| W2 Additional relevant candidates per requisition | SRE-0142: 6, LH-0217: 1 |
| W3 Review burden (irrelevant surfaced + irrelevant via corrections + rejected findings) | 1 |
| W4 Recruiter decisions changed after inspecting evidence | 2 / 3 (67%) |
| W5 Downstream outcomes observed / attributable / not observed | 1 / 0 / 1 |

Recruiter decisions and downstream outcomes are reported separately from independent review. No downstream outcome is attributed to Screening Assurance unless the partner's records mark it attributable, and none implies causation.

## 8. By scenario

| Scenario | Cases | Resolved labels | Interpretable | Relevant surfaced | Relevant missed | Irrelevant surfaced | Baseline missed relevant | Recovered | Findings confirmed | Violations |
|---|---|---|---|---|---|---|---|---|---|---|
| customer-success | CSM-0388 | 4 | no — sample too small | 2 | 0 | 0 | 0 | 0 | 1 | 0 |
| software-infrastructure | SRE-0142 | 17 | yes | 11 | 0 | 0 | 6 | 6 | 3 | 0 |
| transportation | LH-0217 | 6 | no — sample too small | 2 | 0 | 0 | 1 | 1 | 2 | 0 |

## 9. Versions and inputs per case

| Case | Requisition | Policy | Decisions snapshot | Product run sha256 | Inputs |
|---|---|---|---|---|---|
| SRE-0142 | REQ-SRE-0142 | 2026.2 | none | `11e2ad9e62bf` | candidates `e8a26cd2f5`, policy `c85694290b`, pool `abaa9b5a4f`, requisition `7fd307af5b` |
| LH-0217 | REQ-LH-0217 | 2026.2 | none | `58d76a3f5a86` | candidates `8bce53d7f8`, policy `c85694290b`, pool `02bdef3822`, requisition `8de4135f2e` |
| CSM-0388 | REQ-CSM-0388 | 2026.2 | supplied | `ae91cc7e9735` | candidates `d0c43eb763`, decisions `692a131b05`, policy `c85694290b`, requisition `90a96629fb` |

## 10. Limitations, sample size and unresolved items

- Synthetic dataset: labels were authored alongside the fixtures. These results test the measurement loop and must not be reported as design-partner evidence or real-world accuracy.
- 11 candidate(s) have no resolved relevance label (unassessable, unresolved or unreviewed); they are excluded from rates and listed, not treated as positive or negative.
- No baseline available for CSM-0388; baseline comparisons exclude these cases.
- 29 screening-risk finding(s) were not reviewed and are never counted as confirmed.
- Sample too small for interpretation (< 10 resolved labels) in: customer-success, transportation.
- The product view is a deterministic re-run of the dataset inputs. Simulated corrections are not changes to the employer's screening process.
- Screening rules come from supplied exports or documentation, not a live ATS audit.
- Unresolved or unknown candidates: SRE-0142:C-107 (unresolved), SRE-0142:C-112 (unreviewed), SRE-0142:C-114 (unassessable), SRE-0142:P-205 (unassessable), SRE-0142:P-207 (unreviewed), SRE-0142:P-209 (unreviewed), LH-0217:P-303 (unassessable), CSM-0388:C-201 (unreviewed), CSM-0388:C-205 (unreviewed), CSM-0388:C-206 (unreviewed), CSM-0388:C-207 (unassessable)

## Metric definitions

| ID | Metric | Numerator | Denominator | Eligibility | Unknown handling | Minimum evidence |
|---|---|---|---|---|---|---|
| D1 | Relevant candidates surfaced for human review | Candidates whose resolved label is relevant and whose product group is direct, transferable or insufficient | Candidates whose resolved label is relevant and who are eligible for the product (not blocked, not already in active ATS review) | All candidates in the case inputs with a resolved relevance label | Unreviewed, unresolved and unassessable candidates are excluded from both numerator and denominator and reported in D4/D6 | At least one independent review, or an adjudication where reviewers disagree |
| D2 | Relevant candidates still missed by the product | Eligible candidates resolved relevant whose product group is not_surfaced | Same as D1 | As D1 | As D1 | As D1 |
| D3 | Irrelevant candidates surfaced for additional review | Candidates resolved not_relevant whose product group is direct, transferable or insufficient | Surfaced candidates with a resolved label of relevant or not_relevant | Product-surfaced candidates | Surfaced candidates without a resolved label are reported in D4, not here | As D1 |
| D4 | Surfaced candidates whose relevance is not established | Surfaced candidates whose label is unassessable, unresolved or unreviewed | All surfaced candidates | Product-surfaced candidates | This metric is the unknown bucket; never counted as success or failure | None |
| D5 | Results that still require human verification | Candidates in the transferable or insufficient groups | All surfaced candidates | Product-surfaced candidates | Not label-dependent | None |
| B1 | Relevant candidates the existing process missed | Candidates resolved relevant whose baseline outcome is rejected, deprioritized or not_reviewed with basis observed | Candidates resolved relevant with an observed baseline outcome | Cases whose baseline source is not 'not_available' | Inferred baseline outcomes are reported separately (B1-inferred); unknown baselines and pool records that never applied are excluded and counted | Baseline outcome observed in supplied ATS or recruiter records |
| B2 | Of those, surfaced by Screening Assurance | B1 candidates whose product group is direct, transferable or insufficient | B1 numerator | As B1 | As B1 | As B1 |
| B3 | Of those, still missed by Screening Assurance | B1 candidates not surfaced by the product | B1 numerator | As B1 | As B1 | As B1 |
| F1 | Findings independently confirmed | Product screening-risk findings whose resolved review is confirmed | All product screening-risk findings in reviewed cases (including unreviewed ones) | Findings with a screening-risk category | Unreviewed and unresolved findings stay in the denominator and are reported in F4/F5; they are never counted as confirmed | At least one independent review, or an adjudication where reviewers disagree |
| F2 | Findings rejected as unsupported or irrelevant | Resolved review is unsupported or irrelevant | As F1 | As F1 | As F1 | As F1 |
| F3 | Findings deferred or needing more evidence | Resolved review is deferred or needs_more_evidence | As F1 | As F1 | As F1 | As F1 |
| F4 | Findings with unresolved reviewer disagreement | Reviews disagree and no adjudication | As F1 | As F1 | Reported as unknown | Two or more reviews |
| F5 | Findings not reviewed | No review supplied | As F1 | As F1 | Reported as unknown | None |
| F6 | Proposed corrections that reveal relevant candidates for review | Distinct candidates resolved relevant that a simulated correction makes newly eligible for human review | Distinct candidates any simulated correction makes newly eligible | Findings with an evaluable correction simulation | Newly eligible candidates without a resolved label are listed separately | As D1 |
| F7 | Proposed corrections that surface irrelevant candidates | Distinct candidates resolved not_relevant that a simulated correction makes newly eligible | As F6 | As F6 | As F6 | As D1 |
| F8 | Exclusions whose cause cannot be established | Candidates in unexplained-exclusion findings, plus findings whose simulation is not evaluable | Not a rate | All cases | This metric is an unknown bucket | None |
| F9 | Findings without a verified baseline | Screening-risk findings in cases whose baseline is not available, or whose affected candidates have no observed baseline outcome | As F1 | As F1 | These findings may be valid rule-level risks but cannot be tied to an observed exclusion | None |
| V1 | Mandatory-requirement violations | Surfaced or newly eligible candidates whose resolved mandatory disposition is not_met; candidates eligible in a simulation while failing a protected requirement; corrections proposed for protected rules | Not a rate: any occurrence is reported individually | All cases | cannot_verify and unresolved mandatory dispositions are listed separately, not counted as violations or as passes | None |
| V2 | Blocked-record or policy violations | Blocked (unauthorized, expired or stale) pool records that appear in a surfaced group or simulation; surfaced candidates whose evidence relies on an equivalency the employer policy rejects | Not a rate: any occurrence is reported individually | All cases | Not label-dependent | None |
| W1 | Recruiter review time, baseline vs. assisted | Sum of assisted minutes and of baseline minutes over cases with measured time | Cases with measured: true | Cases whose partner supplied both measurements | Unmeasured cases are counted, never imputed | Partner timing method stated |
| W2 | Additional relevant candidates identified per requisition | B2 per case | Cases with an observed baseline | As B1 | As B1 | As B1 |
| W3 | Review burden from irrelevant candidates and unsupported findings | D3 numerator + F7 numerator + F2 numerator | Not a rate | All cases | Unknown-relevance candidates (D4) are reported beside it | As D1/F1 |
| W4 | Recruiter decisions changed after inspecting evidence | Recorded recruiter decisions with changed_after_evidence: true | Recorded recruiter decisions | Cases with recruiter decisions | Cases without decisions are counted, not imputed | Recorded decisions |
| W5 | Downstream outcomes (observed only) | Observed downstream outcomes by type; attributable ones counted separately | Not a rate | Entries with observed: true | Unobserved entries are counted and excluded; no causal claim is made | Partner records |
