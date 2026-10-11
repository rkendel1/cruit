# Screening assurance — portfolio overview

- Requisitions reviewed: **4**
- Findings awaiting decisions: **17**
- Confirmed screening inconsistencies: **15**
- Approved corrections: **15**
- Candidate-review opportunities: **10**
- Measured outcomes: **1**

## Requisitions

| Requisition | Job family | L1 | L2 | L3 | Surfaced | Pending | Knowledge |
|---|---|---|---|---|---|---|---|
| REQ-CSM-0388 Customer Success Manager, Mid-Market | customer-success | 3 | 8 | 0 | 3/8 | 7 | `core@1.1.0+8a94e741e4` |
| REQ-LH-0217 Linehaul Operations Supervisor | logistics-operations | 0 | 4 | 0 | 1/4 | 4 | `core@1.1.0+8a94e741e4` |
| REQ-RO-0455 Revenue Operations Manager | revenue-operations | 2 | 3 | 0 | 0/0 | 5 | `core@1.1.0+8a94e741e4` |
| REQ-SRE-0142 Senior Site Reliability Engineer | software-infrastructure | 10 | 12 | 1 | 6/13 | 1 | `core@1.1.0+8a94e741e4` |

## Priority work

Confirmed inconsistencies first (ordered by how many candidate-review opportunities depend on them), then candidates awaiting review.

- **REQ-CSM-0388** `SA-REQ-CSM-0388-7f815e04` (L1) Preferred qualification R4 is enforced as a knockout by Q3 — unlocks 3 candidate(s)
- **REQ-RO-0455** `SA-REQ-RO-0455-4d7c87e1` (L1) Q1 requires 7 years; the posting asks for 5
- **REQ-RO-0455** `SA-REQ-RO-0455-30380d96` (L1) Preferred qualification R3 is enforced as a knockout by Q2
- **REQ-CSM-0388** `SA-REQ-CSM-0388-7f33b017` (L2) Candidate C-202 may meet the requirements through a path the current rules do not recognize
- **REQ-CSM-0388** `SA-REQ-CSM-0388-dc08d1e4` (L2) Candidate C-204 may meet the requirements through a path the current rules do not recognize
- **REQ-CSM-0388** `SA-REQ-CSM-0388-ea6778d8` (L2) Candidate C-207 may meet the requirements through a path the current rules do not recognize
- **REQ-LH-0217** `SA-REQ-LH-0217-6f063ac1` (L2) Candidate C-303 may meet the requirements through a path the current rules do not recognize
- **REQ-SRE-0142** `SA-REQ-SRE-0142-82276566` (L2) Candidate C-110 may meet the requirements through a path the current rules do not recognize

## Recurring screening defects

- `literal_term_missing_variants` in 4 requisitions: REQ-CSM-0388, REQ-LH-0217, REQ-RO-0455, REQ-SRE-0142
- `experience_path_narrower` in 4 requisitions: REQ-CSM-0388, REQ-LH-0217, REQ-RO-0455, REQ-SRE-0142
- `preferred_enforced_as_knockout` in 3 requisitions: REQ-CSM-0388, REQ-RO-0455, REQ-SRE-0142
- `equivalent_path_blocked` in 2 requisitions: REQ-CSM-0388, REQ-SRE-0142
- `unverified_necessity` in 2 requisitions: REQ-CSM-0388, REQ-SRE-0142
- `threshold_inconsistency` in 2 requisitions: REQ-RO-0455, REQ-SRE-0142

## Patterns by job family

- **customer-success**: literal_term_missing_variants ×3, equivalent_path_blocked ×1, credential_stricter_than_requirement ×1, preferred_enforced_as_knockout ×1, experience_path_narrower ×1, unverified_necessity ×1
- **logistics-operations**: literal_term_missing_variants ×2, experience_path_narrower ×1
- **revenue-operations**: literal_term_missing_variants ×2, threshold_inconsistency ×1, preferred_enforced_as_knockout ×1, experience_path_narrower ×1
- **software-infrastructure**: equivalent_path_blocked ×3, rule_narrower_than_requirement ×3, literal_term_missing_variants ×3, preferred_enforced_as_knockout ×2, threshold_inconsistency ×1, unstated_requirement_enforced ×1, experience_path_narrower ×1, unverified_necessity ×1

## Measured outcomes

- REQ-SRE-0142: Measured: 4 of 5 additionally reviewed candidates met the role's requirements
