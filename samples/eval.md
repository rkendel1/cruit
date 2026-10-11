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
