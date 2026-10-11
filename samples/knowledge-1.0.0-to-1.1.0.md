# Knowledge comparison — `core@1.0.0+2d833ad705` → `core@1.1.0+8a94e741e4`

**Regression gate: PASS**


| Metric | Baseline | Candidate | Δ |
|---|---|---|---|
| cases | 4 | 4 | 0 |
| expected findings | 29 | 29 | 0 |
| expected found | 26 | 29 | 3 |
| expected finding recall | 0.897 | 1.0 | 0.103 |
| forbidden violations | 0 | 0 | 0 |
| guardrail violations | 0 | 0 | 0 |
| candidates flagged | 9 | 11 | 2 |
| true positives | 8 | 10 | 2 |
| false positives | 0 | 0 | 0 |
| missed qualified | 2 | 0 | -2 |
| candidate precision | 1.0 | 1.0 | 0.0 |
| candidate recall | 0.8 | 1.0 | 0.2 |

## customer-success

- ➕ `SA-REQ-CSM-0388-7da18d53` R1 accepts equivalent experience, but Q1 has no equivalent path
- ➕ `SA-REQ-CSM-0388-dc08d1e4` Candidate C-204 may meet the requirements through a path the current rules do not recognize
- ✎ `SA-REQ-CSM-0388-309d1f67` Q2 counts experience only under specific job titles: {'affected': [['C-202'], ['C-202', 'C-204']]}
- Newly flagged for review: C-204
- ✅ expected finding now found: equivalent_path_blocked Q1
- ✅ expected finding now found: candidate_review_opportunity C-204

## linehaul-protected-license

_No change._

## revops-prepublication

_No change._

## sre-incident-management

- ➕ `SA-REQ-SRE-0142-36d39631` Candidate C-106 may meet the requirements through a path the current rules do not recognize
- ✎ `SA-REQ-SRE-0142-5302d6be` R2 accepts equivalent experience, but Q3 has no equivalent path: {'affected': [['C-103', 'C-104', 'C-107'], ['C-103', 'C-104', 'C-106', 'C-107']]}
- ✎ `SA-REQ-SRE-0142-5f56524c` Candidate C-102 may meet the requirements through a path the current rules do not recognize: {'confidence': ['medium', 'high']}
- ✎ `SA-REQ-SRE-0142-b05a4c5a` Q1 matches literally and misses recognized variants of Site reliability engineering: {'affected': [['C-111'], ['C-102', 'C-111']]}
- Newly flagged for review: C-106
- ✅ expected finding now found: candidate_review_opportunity C-106

## Screening risks (forward simulation)

> **SYNTHETIC FIXTURE RESULTS — not a measure of real-world accuracy**

| Metric | Baseline | Candidate |
|---|---|---|
| relevant surfaced | 7 | 9 |
| relevant missed | 2 | 0 |
| irrelevant surfaced | 0 | 0 |
| mandatory violations | 0 | 0 |
| policy violations | 0 | 0 |
| needs human verification | 12 | 13 |
| unknown cause | 2 | 2 |
| expectations | 17 | 17 |
| expectations met | 15 | 17 |
| relevant recall | 0.778 | 1.0 |

## Candidate rediscovery

> **SYNTHETIC FIXTURE RESULTS — not a measure of real-world accuracy**

| Metric | Baseline | Candidate |
|---|---|---|
| cases | 2 | 2 |
| relevant surfaced | 11 | 13 |
| relevant missed | 2 | 0 |
| irrelevant surfaced | 0 | 0 |
| overclaimed certainty | 0 | 0 |
| mandatory violations | 0 | 0 |
| blocked violations | 0 | 0 |
| needs human verification | 6 | 6 |
| group mismatches | 2 | 0 |
| relevant recall | 0.846 | 1.0 |
| recruiter dispositions | not measured in fixtures | not measured in fixtures |
| recruiter minutes | not measured in fixtures | not measured in fixtures |

### linehaul-rediscovery

_No change._

### sre-rediscovery

- C-102: transferable → direct
- C-106: not_surfaced → transferable
- P-208: not_surfaced → direct

## Knowledge records changed

```
Knowledge diff core@1.0.0+2d833ad705 -> core@1.1.0+8a94e741e4
  + eq.customer-success.b2b-account-management  [equivalencies]
  ~ eq.incident-management.operational-crisis-response  [equivalencies] v1->v2: indicators, provenance, version
  ~ term.post-incident-review  [synonyms] v1->v2: ambiguities, provenance, rationale, variants, version
  ~ term.site-reliability-engineering  [synonyms] v1->v2: provenance, rationale, variants, version
```
