# Evaluation — knowledge `core@1.1.0+8a94e741e4`

**Result: PASS**


| Metric | Value |
|---|---|
| cases | 4 |
| expected findings | 28 |
| expected found | 28 |
| expected finding recall | 1.0 |
| forbidden violations | 0 |
| guardrail violations | 0 |
| candidates flagged | 10 |
| true positives | 10 |
| false positives | 0 |
| missed qualified | 0 |
| candidate precision | 1.0 |
| candidate recall | 1.0 |

## customer-success

Customer Success Manager requisition documented by the recruiter. A literal "customer success" filter, a title-based prioritization and a certification filter where the posting asks only for proficiency. Includes an employer policy that rejects one general equivalency (support escalation leadership), and profiles whose transferable skills are real but insufficient for the role.

- Candidates flagged for review: C-202, C-204
- True positives: C-202, C-204; false positives: —; missed qualified: —
- Precision 1.0 · recall 1.0
- Expected findings: 7/7 found
- Forbidden findings produced: 0

## linehaul-protected-license

Linehaul supervisor requisition with a legally required Class A CDL. The engine may recognize spelling variants of the license, but must never propose an alternative path for it or surface anyone who lacks it — however strong their supervisory experience.

- Candidates flagged for review: C-303
- True positives: C-303; false positives: —; missed qualified: —
- Precision 1.0 · recall 1.0
- Expected findings: 3/3 found
- Forbidden findings produced: 0

## revops-prepublication

Pre-publication design review with no candidates: the engine must find rule defects from the requisition and knowledge alone, and must not invent candidate findings.

- Candidates flagged for review: —
- True positives: —; false positives: —; missed qualified: —
- Precision None · recall None
- Expected findings: 4/4 found
- Forbidden findings produced: 0

## sre-incident-management

Senior SRE requisition with literal keyword filters, a title-based experience rule stricter than the posting, knockouts on preferred qualifications, and an unstated tool requirement. Candidate pool mixes conventional SREs, adjacent titles, and nontraditional incident leaders from healthcare, logistics and the military, plus participation-only and under-experienced profiles that must not be surfaced.

- Candidates flagged for review: C-102, C-103, C-106, C-108, C-109, C-110, C-113
- True positives: C-102, C-103, C-106, C-108, C-109, C-110, C-113; false positives: —; missed qualified: —
- Precision 1.0 · recall 1.0
- Expected findings: 14/14 found
- Forbidden findings produced: 0

## Candidate rediscovery

> **SYNTHETIC FIXTURE RESULTS — not a measure of real-world accuracy**

| Metric | Value |
|---|---|
| cases | 2 |
| relevant surfaced | 13 |
| relevant missed | 0 |
| irrelevant surfaced | 0 |
| overclaimed certainty | 0 |
| mandatory violations | 0 |
| blocked violations | 0 |
| needs human verification | 6 |
| group mismatches | 0 |
| relevant recall | 1.0 |
| recruiter dispositions | not measured in fixtures |
| recruiter minutes | not measured in fixtures |

### linehaul-rediscovery

SYNTHETIC. Rediscovery for the Linehaul Operations Supervisor requisition, where a Class A CDL is legally required. A strong operations leader without the license must not be surfaced; a record whose credentials were not supplied may only appear as "insufficient evidence".

- relevant surfaced: C-303, P-301
- relevant missed: —
- irrelevant surfaced: —
- overclaimed certainty: —
- mandatory violations: —
- blocked violations: —
- needs human verification: C-303, P-303
- group mismatches: —

| Fixture | Type | Group |
|---|---|---|
| P-301 | direct evidence with the required license | direct |
| P-302 | missing a genuine mandatory qualification (license absent from a complete credential list) | not_surfaced |
| P-303 | license cannot be verified (credentials not supplied) | insufficient |
| C-302 | strong supervisor without the license (current applicant) | not_surfaced |

### sre-rediscovery

SYNTHETIC. Rediscovery for the Senior SRE requisition across current applicants and an authorized talent-CRM pool. Covers direct evidence, different titles, transferable experience, look-alikes without necessary evidence, partial records, and stale, unauthorized and expired records that must never be surfaced for action.

- relevant surfaced: C-102, C-103, C-106, C-108, C-109, C-110, C-113, P-201, P-202, P-203, P-208
- relevant missed: —
- irrelevant surfaced: —
- overclaimed certainty: —
- mandatory violations: —
- blocked violations: —
- needs human verification: C-103, C-106, P-203, P-205
- group mismatches: —

| Fixture | Type | Group |
|---|---|---|
| P-201 | direct evidence (prior applicant, conventional title) | direct |
| P-202 | different title, relevant evidence | direct |
| P-203 | plausibly transferable experience (utility grid control room) needing review | transferable |
| P-204 | appears similar (incident tickets, systems dashboards) but lacks necessary evidence | not_surfaced |
| P-205 | insufficient evidence (partial talent-community profile) | insufficient |
| P-206 | stale record (evidence older than 730 days) | blocked |
| P-207 | unauthorized record (original requisition only) | blocked |
| P-209 | expired authorization | blocked |
| P-208 | discovered only after knowledge 1.1.0 (production reliability title variant) | direct |
| C-107 | conventional title, below the posted experience threshold | not_surfaced |
