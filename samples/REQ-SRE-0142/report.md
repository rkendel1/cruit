# Requisition assurance report — Senior Site Reliability Engineer (REQ-SRE-0142)

Job family `software-infrastructure` · employer `northwind` · knowledge `core@1.1.0+8a94e741e4` (approved) · engine 0.2.0 · run 2026-11-03T12:00:00Z

> This report recommends changes and human review. It does not reject, advance or hire anyone, and it does not claim any candidate was wrongly excluded. Level 1 findings are established by the supplied materials; Level 2 findings are risks that need human judgement; Level 3 findings are measured outcomes.

## Summary

- **10** demonstrable inconsistencies (Level 1)
- **12** missed-talent risks and review opportunities (Level 2), including **6** candidate(s) of 14 assessed surfaced for human review
- **1** measured outcomes (Level 3)
- **1** findings awaiting a human decision

**Inputs received:** job description: `supplied`, screening configuration: `ats_export_verified`, candidate evidence: `authorized_sample`

**Limitations of this run**
- Requirement R6 treated as 'preferred' because of human decision on SA-REQ-SRE-0142-ff4b8adc.
- Screening rules come from a supplied ATS configuration export; this is not a live ATS audit, and the live configuration may have changed since export.
- Candidate evidence is a sample; candidate counts do not represent the full applicant pool.
- Candidate evidence is matched deterministically against the knowledge pack; language-model interpretation is not used in this run.

## 1. Requirements and stated intent

| ID | Requirement | Stated as | Proposed classification | Basis |
|---|---|---|---|---|
| R1 | 5+ years of site reliability engineering or production operations experience. | required | Demonstrable through alternatives | posting accepts equivalent experience |
| R2 | Experience leading incident management, including post-incident reviews. | required | Demonstrable through alternatives | posting accepts equivalent experience |
| R3 | Proficiency with infrastructure as code (Terraform or equivalent). | required | Demonstrable through alternatives | posting accepts equivalent experience |
| R4 | Experience operating Kubernetes. | preferred | Preferred | stated as preferred in the posting |
| R5 | Bachelor's degree in computer science or a related field, or equivalent practical experience. | preferred | Preferred | stated as preferred in the posting |
| R6 | Experience in the logistics or freight industry. | preferred | Preferred | set by recorded human decision |

🔒 = protected (legal, licensing or employer non-negotiable). No alternative path is ever proposed for protected requirements.

## 2. Screening rules inspected

| Rule | Type | Action | Linked requirement | Status | Findings |
|---|---|---|---|---|---|
| Q1 | keyword_filter | reject | R1 | correction proposed | 3 |
| Q2 | minimum_experience | reject | R1 | correction proposed | 4 |
| Q3 | knockout_question | reject | R2 | correction proposed | 1 |
| Q4 | knockout_question | reject | R5 | correction proposed | 2 |
| Q5 | keyword_filter | reject | R3 | correction proposed | 2 |
| Q6 | knockout_question | reject | R4 | correction proposed | 1 |
| Q7 | keyword_filter | reject | — (none) | correction proposed | 1 |

## 3. Confirmed inconsistencies and protected requirements

### R1 accepts equivalent experience, but Q1 has no equivalent path

`SA-REQ-SRE-0142-704c5892` · Level 1 · Demonstrable inconsistency · confidence **high** · check `equivalent_path_blocked`

The posting accepts equivalent experience for R1, but rule Q1 only recognizes the listed terms and has no route for recognized equivalent experience.

**Evidence**
- `requirement:R1` — 5+ years of site reliability engineering or production operations experience.
- `rule:Q1` — Résumé must mention site reliability engineer or SRE.

**Proposed action:** Add an equivalent-evidence path (e.g. a follow-up question or recruiter review route) so applicants with equivalent experience are reviewed rather than rejected.

**Expected benefit:** Restores the equivalency the employer already committed to in the posting.  
**Trade-off:** Equivalent-path applicants need recruiter verification time.

**Screening-risk category:** Potentially equivalent experience

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 13: C-102, C-103, C-104, C-105, C-106, C-110, C-111, C-112, P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 4: C-102, C-103, C-110, P-203 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 1: P-203 (pool, hypothetical) |
| Newly eligible for human review | 3: C-102, C-103, C-110 |

- C-102: eligible together with the proposed corrections to Q2, Q5
- C-103: eligible together with the proposed corrections to Q2, Q3, Q4, Q6, Q7
- C-110: eligible together with the proposed corrections to Q2, Q7

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R1, rule:Q1. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.site-reliability.production-operations.</sub>

Decision: **accepted** by recruiter.lee@northwind.example (2026-10-12T15:10:00Z): Posting already accepts equivalent experience; add a recruiter-review route for production-operations résumés.

### Q1 is narrower than R1: it ignores Production operations

`SA-REQ-SRE-0142-9164e1d0` · Level 1 · Demonstrable inconsistency · confidence **high** · check `rule_narrower_than_requirement`

Requirement R1 can be met through Production operations, but rule Q1 only recognizes 'site reliability engineer', 'SRE'.

**Evidence**
- `requirement:R1` — 5+ years of site reliability engineering or production operations experience.
- `rule:Q1` — Résumé must mention site reliability engineer or SRE.

**Proposed action:** Extend the rule to recognize: Production operations, IT operations, systems operations, infrastructure operations, operations engineering, platform operations, network operations.

**Expected benefit:** Applicants who meet the requirement as written are no longer filtered out.  
**Trade-off:** Broader matching may increase review volume; terms are limited to the posted requirement.

**Limitations**
- Concept recognition uses the knowledge pack; review the proposed terms before adopting them.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 13: C-102, C-103, C-104, C-105, C-106, C-110, C-111, C-112, P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 7: C-103, C-104, C-106, C-110, P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 2: C-104, P-204 (pool, hypothetical) |
| Relevant evidence, but still fail other supplied rules | 2: P-202 (pool, hypothetical), P-203 (pool, hypothetical) |
| Newly eligible for human review | 3: C-103, C-106, C-110 |

- C-103: eligible together with the proposed corrections to Q2, Q3, Q4, Q6, Q7
- C-106: eligible together with the proposed corrections to Q2, Q3, Q4, Q6, Q7
- C-110: eligible together with the proposed corrections to Q2, Q7

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R1, rule:Q1. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.production-operations.</sub>

Decision: **accepted** by recruiter.lee@northwind.example (2026-10-12T15:11:00Z): R1 explicitly allows production operations; the filter should too.

### Q2 is narrower than R1: it ignores Production operations

`SA-REQ-SRE-0142-9403725f` · Level 1 · Demonstrable inconsistency · confidence **high** · check `rule_narrower_than_requirement`

Requirement R1 can be met through Production operations, but rule Q2 only recognizes 'site reliability engineer', 'SRE'.

**Evidence**
- `requirement:R1` — 5+ years of site reliability engineering or production operations experience.
- `rule:Q2` — At least 7 years in Site Reliability Engineer roles (by job title).

**Proposed action:** Extend the rule to recognize: Production operations, IT operations, systems operations, infrastructure operations, operations engineering, platform operations, network operations.

**Expected benefit:** Applicants who meet the requirement as written are no longer filtered out.  
**Trade-off:** Broader matching may increase review volume; terms are limited to the posted requirement.

**Limitations**
- Concept recognition uses the knowledge pack; review the proposed terms before adopting them.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 17: C-102, C-103, C-104, C-105, C-106, C-107, C-108, C-109, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 0 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 0 |

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R1, rule:Q2. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.production-operations.</sub>

Decision: **accepted** by recruiter.lee@northwind.example (2026-10-12T15:13:00Z): Consistent with R1.

### Q2 requires 7 years; the posting asks for 5

`SA-REQ-SRE-0142-d15dcf14` · Level 1 · Demonstrable inconsistency · confidence **high** · check `threshold_inconsistency`

Requirement R1 states 5+ years, but rule Q2 enforces 7 years.

**Evidence**
- `requirement:R1` — 5+ years of site reliability engineering or production operations experience.
- `rule:Q2` — years: 7 — At least 7 years in Site Reliability Engineer roles (by job title).

**Proposed action:** Align the rule threshold with the posted requirement (5 years), or update the posting if the higher threshold is genuinely required.

**Expected benefit:** Applicants who meet the posted threshold are no longer silently excluded.  
**Trade-off:** None if the posting reflects the real need.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 17: C-102, C-103, C-104, C-105, C-106, C-107, C-108, C-109, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 3: C-108, C-109, P-201 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 1: P-201 (pool, hypothetical) |
| Newly eligible for human review | 2: C-108, C-109 |

- C-108: eligible together with the proposed corrections to Q4
- C-109: eligible together with the proposed corrections to Q6

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R1, rule:Q2. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:00:00Z): Five years is the real bar; seven was copied from the staff-level req.

### R2 accepts equivalent experience, but Q3 has no equivalent path

`SA-REQ-SRE-0142-5302d6be` · Level 1 · Demonstrable inconsistency · confidence **high** · check `equivalent_path_blocked`

The posting accepts equivalent experience for R2, but rule Q3 rejects applicants who answer or hold otherwise, regardless of equivalent evidence.

**Evidence**
- `requirement:R2` — Experience leading incident management, including post-incident reviews.
- `rule:Q3` — Have you served as incident commander for a software production environment?

**Proposed action:** Add an equivalent-evidence path (e.g. a follow-up question or recruiter review route) so applicants with equivalent experience are reviewed rather than rejected.

**Expected benefit:** Restores the equivalency the employer already committed to in the posting.  
**Trade-off:** Equivalent-path applicants need recruiter verification time.

**Screening-risk category:** Potentially equivalent experience

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-103, C-104, C-105, C-106, C-107, C-111, C-112 |
| Would pass the proposed rule | 4: C-103, C-104, C-106, C-107 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 7: C-114, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Pass the rule, but relevance not established | 2: C-104, C-107 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 2: C-103, C-106 |

- C-103: eligible together with the proposed corrections to Q1, Q2, Q4, Q6, Q7
- C-106: eligible together with the proposed corrections to Q1, Q2, Q4, Q6, Q7

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Pool records have no recorded answers to knockout questions, so the supplied question cannot be evaluated for them.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R2, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.incident-management.operational-crisis-response.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:05:00Z): Some of our best incident leads came from operations. Route 'no' answers with crisis-leadership evidence to review.

### Preferred qualification R5 is enforced as a knockout by Q4

`SA-REQ-SRE-0142-3bc61a83` · Level 1 · Demonstrable inconsistency · confidence **high** · check `preferred_enforced_as_knockout`

Requirement R5 is stated as preferred, but rule Q4 rejects applicants who do not meet it.

**Evidence**
- `requirement:R5` — stated_as: preferred — Bachelor's degree in computer science or a related field, or equivalent practical experience.
- `rule:Q4` — action: reject — Do you hold a bachelor's degree in computer science?

**Proposed action:** Convert the rule into a scoring or ranking signal, or reclassify the requirement as essential with a documented rationale.

**Expected benefit:** Applicants who meet all essential requirements are no longer rejected for lacking a preference.  
**Trade-off:** More applicants reach review; ranking should still favour the preferred qualification.

**Screening-risk category:** Preferred criterion enforced as a knockout

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 6: C-103, C-104, C-105, C-106, C-108, C-111 |
| Would pass the proposed rule | 6: C-103, C-104, C-105, C-106, C-108, C-111 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 6: P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Pass the rule, but relevance not established | 3: C-104, C-105, C-111 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 3: C-103, C-106, C-108 |

- C-103: eligible together with the proposed corrections to Q1, Q2, Q3, Q6, Q7
- C-106: eligible together with the proposed corrections to Q1, Q2, Q3, Q6, Q7
- C-108: eligible together with the proposed corrections to Q2

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Pool records have no recorded answers to knockout questions, so the supplied question cannot be evaluated for them.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R5, rule:Q4. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:06:00Z): Degree is a preference; use it for ranking only.

### R5 accepts equivalent experience, but Q4 has no equivalent path

`SA-REQ-SRE-0142-512cd6d3` · Level 1 · Demonstrable inconsistency · confidence **high** · check `equivalent_path_blocked`

The posting accepts equivalent experience for R5, but rule Q4 rejects applicants who answer or hold otherwise, regardless of equivalent evidence.

**Evidence**
- `requirement:R5` — Bachelor's degree in computer science or a related field, or equivalent practical experience.
- `rule:Q4` — Do you hold a bachelor's degree in computer science?

**Proposed action:** Add an equivalent-evidence path (e.g. a follow-up question or recruiter review route) so applicants with equivalent experience are reviewed rather than rejected.

**Expected benefit:** Restores the equivalency the employer already committed to in the posting.  
**Trade-off:** Equivalent-path applicants need recruiter verification time.

**Limitations**
- Equivalent practical experience is interpreted as meeting the posted experience requirement(s) R1.

**Screening-risk category:** Potentially equivalent experience

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 6: C-103, C-104, C-105, C-106, C-108, C-111 |
| Would pass the proposed rule | 5: C-103, C-104, C-106, C-108, C-111 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 6: P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Pass the rule, but relevance not established | 2: C-104, C-111 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 3: C-103, C-106, C-108 |

- C-103: eligible together with the proposed corrections to Q1, Q2, Q3, Q6, Q7
- C-106: eligible together with the proposed corrections to Q1, Q2, Q3, Q6, Q7
- C-108: eligible together with the proposed corrections to Q2

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Pool records have no recorded answers to knockout questions, so the supplied question cannot be evaluated for them.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R5, rule:Q4. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.site-reliability.production-operations.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:06:30Z): Same change as the knockout removal.

### Q5 is narrower than R3: it ignores Infrastructure as code

`SA-REQ-SRE-0142-f01e2bd0` · Level 1 · Demonstrable inconsistency · confidence **high** · check `rule_narrower_than_requirement`

Requirement R3 can be met through Infrastructure as code, but rule Q5 only recognizes 'Terraform'.

**Evidence**
- `requirement:R3` — Proficiency with infrastructure as code (Terraform or equivalent).
- `rule:Q5` — Résumé must mention Terraform.

**Proposed action:** Extend the rule to recognize: Infrastructure as code, infrastructure automation, IaC, Ansible, AWS CloudFormation, CloudFormation, Pulumi, Terraform, HashiCorp Terraform, OpenTofu.

**Expected benefit:** Applicants who meet the requirement as written are no longer filtered out.  
**Trade-off:** Broader matching may increase review volume; terms are limited to the posted requirement.

**Limitations**
- Concept recognition uses the knowledge pack; review the proposed terms before adopting them.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-102, C-104, C-105, C-111, C-112, P-203 (pool, hypothetical), P-204 (pool, hypothetical) |
| Would pass the proposed rule | 2: C-102, P-203 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 1: P-203 (pool, hypothetical) |
| Newly eligible for human review | 1: C-102 |

- C-102: eligible together with the proposed corrections to Q1, Q2

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R3, rule:Q5. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.infrastructure-as-code.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:07:00Z): Pulumi, CloudFormation and Ansible experience transfers; we said 'or equivalent'.

### Preferred qualification R4 is enforced as a knockout by Q6

`SA-REQ-SRE-0142-48360a3a` · Level 1 · Demonstrable inconsistency · confidence **high** · check `preferred_enforced_as_knockout`

Requirement R4 is stated as preferred, but rule Q6 rejects applicants who do not meet it.

**Evidence**
- `requirement:R4` — stated_as: preferred — Experience operating Kubernetes.
- `rule:Q6` — action: reject — Do you have hands-on Kubernetes experience?

**Proposed action:** Convert the rule into a scoring or ranking signal, or reclassify the requirement as essential with a documented rationale.

**Expected benefit:** Applicants who meet all essential requirements are no longer rejected for lacking a preference.  
**Trade-off:** More applicants reach review; ranking should still favour the preferred qualification.

**Screening-risk category:** Preferred criterion enforced as a knockout

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-103, C-104, C-105, C-106, C-109, C-111, C-112 |
| Would pass the proposed rule | 7: C-103, C-104, C-105, C-106, C-109, C-111, C-112 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 6: P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Pass the rule, but relevance not established | 4: C-104, C-105, C-111, C-112 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 3: C-103, C-106, C-109 |

- C-103: eligible together with the proposed corrections to Q1, Q2, Q3, Q4, Q7
- C-106: eligible together with the proposed corrections to Q1, Q2, Q3, Q4, Q7
- C-109: eligible together with the proposed corrections to Q2

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Pool records have no recorded answers to knockout questions, so the supplied question cannot be evaluated for them.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R4, rule:Q6. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:08:00Z): Kubernetes is learnable; Nomad experience is fine.

### Rule Q7 enforces a requirement the job description does not state

`SA-REQ-SRE-0142-99df8968` · Level 1 · Demonstrable inconsistency · confidence **high** · check `unstated_requirement_enforced`

Screening rule Q7 (keyword_filter, action: reject) screens on 'Datadog', but no posted requirement corresponds to it.

**Evidence**
- `rule:Q7` — Résumé must mention Datadog.

**Proposed action:** Confirm whether this is a genuine job requirement. If it is, add it to the posted requirements with its rationale; if not, remove the rule or convert it to a preference.

**Expected benefit:** Applicants are screened only on requirements they were told about.  
**Trade-off:** If the requirement is genuine, removing the rule would admit unqualified applicants; confirm first.

**Limitations**
- The requirement may be genuine but undocumented; only the employer can confirm.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 13: C-103, C-104, C-105, C-106, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 13: C-103, C-104, C-105, C-106, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 1: P-205 (pool, hypothetical) |
| Pass the rule, but relevance not established | 5: C-104, C-105, C-111, C-112, P-204 (pool, hypothetical) |
| Relevant evidence, but still fail other supplied rules | 4: P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-208 (pool, hypothetical) |
| Newly eligible for human review | 3: C-103, C-106, C-110 |

- C-103: eligible together with the proposed corrections to Q1, Q2, Q3, Q4, Q6
- C-106: eligible together with the proposed corrections to Q1, Q2, Q3, Q4, Q6
- C-110: eligible together with the proposed corrections to Q1, Q2

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q7. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:10:00Z): Stale filter from an earlier requisition; we run Prometheus and any monitoring experience transfers.

## 4. Potential missed-talent risks

### Q1 matches literally and misses recognized variants of Site reliability engineering

`SA-REQ-SRE-0142-b05a4c5a` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q1 matches only 'site reliability engineer', 'SRE'. The knowledge base records 3 equivalent term(s) for Site reliability engineering that the rule does not recognize.

**Evidence**
- `knowledge:skill.site-reliability-engineering` — recognized variant(s): Site reliability engineering, production reliability engineering, production reliability engineer

**Proposed action:** Add recognized variants to the rule: Site reliability engineering, production reliability engineering, production reliability engineer.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- 'reliability engineering': Deliberately not a variant: in manufacturing and hardware contexts it means equipment reliability.
- The presence of a related term does not prove that the candidate possesses the required experience.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 13: C-102, C-103, C-104, C-105, C-106, C-110, C-111, C-112, P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 3: C-102, C-111, P-208 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 1: C-111 |
| Relevant evidence, but still fail other supplied rules | 1: P-208 (pool, hypothetical) |
| Newly eligible for human review | 1: C-102 |

- C-102: eligible together with the proposed corrections to Q2, Q5

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q1, knowledge:skill.site-reliability-engineering, knowledge:term.site-reliability-engineering. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.site-reliability-engineering, term.site-reliability-engineering.</sub>

Decision: **accepted** by recruiter.lee@northwind.example (2026-10-12T15:12:00Z): Same function, different title.

### Q2 matches literally and misses recognized variants of Site reliability engineering

`SA-REQ-SRE-0142-e3e3d885` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q2 matches only 'site reliability engineer', 'SRE'. The knowledge base records 3 equivalent term(s) for Site reliability engineering that the rule does not recognize.

**Evidence**
- `knowledge:skill.site-reliability-engineering` — recognized variant(s): Site reliability engineering, production reliability engineering, production reliability engineer

**Proposed action:** Add recognized variants to the rule: Site reliability engineering, production reliability engineering, production reliability engineer.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- 'reliability engineering': Deliberately not a variant: in manufacturing and hardware contexts it means equipment reliability.
- The presence of a related term does not prove that the candidate possesses the required experience.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 17: C-102, C-103, C-104, C-105, C-106, C-107, C-108, C-109, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 0 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 0 |

<sub>A reviewer rejected this correction; it is excluded from the combined simulation.</sub>  
<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q2, knowledge:skill.site-reliability-engineering, knowledge:term.site-reliability-engineering. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.site-reliability-engineering, term.site-reliability-engineering.</sub>

Decision: **rejected** by recruiter.lee@northwind.example (2026-10-12T15:13:30Z): Moot: Q2 will count responsibilities across the résumé (see the experience-path finding), so adding title variants is unnecessary.

### Q2 counts experience only under specific job titles

`SA-REQ-SRE-0142-a0ac83a9` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `experience_path_narrower`

Rule Q2 only counts experience held under the titles 'site reliability engineer', 'SRE'. The underlying capability can be demonstrated under other titles and in other domains.

**Evidence**
- `rule:Q2` — At least 7 years in Site Reliability Engineer roles (by job title).

**Proposed action:** Count relevant experience by responsibilities, not titles: match recognized terminology across the full résumé and route equivalency evidence to recruiter review.

**Expected benefit:** Candidates whose titles differ from the conventional path reach human review.  
**Trade-off:** Responsibility-based matching needs recruiter verification; expect modest extra review time.

**Limitations**
- Whether alternative experience is equivalent must be judged by a recruiter or hiring manager.
- Title-based counting may reflect a deliberate employer choice; confirm intent.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 17: C-102, C-103, C-104, C-105, C-106, C-107, C-108, C-109, C-110, C-111, C-112, P-201 (pool, hypothetical), P-202 (pool, hypothetical), P-203 (pool, hypothetical), P-204 (pool, hypothetical), P-205 (pool, hypothetical), P-208 (pool, hypothetical) |
| Would pass the proposed rule | 1: P-203 (pool, hypothetical) |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 1: P-203 (pool, hypothetical) |
| Newly eligible for human review | 0 |

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q2, requirement:R1. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.site-reliability.production-operations.</sub>

Decision: **accepted** by hm.okafor@northwind.example (2026-10-12T16:02:00Z): Count responsibilities, not titles; recruiter verifies scope.

### Q5 matches literally and misses recognized variants of Terraform

`SA-REQ-SRE-0142-9d626aeb` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q5 matches only 'Terraform'. The knowledge base records 2 equivalent term(s) for Terraform that the rule does not recognize.

**Evidence**
- `knowledge:skill.terraform` — recognized variant(s): HashiCorp Terraform, OpenTofu

**Proposed action:** Add recognized variants to the rule: HashiCorp Terraform, OpenTofu.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-102, C-104, C-105, C-111, C-112, P-203 (pool, hypothetical), P-204 (pool, hypothetical) |
| Would pass the proposed rule | 0 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 0 |

<sub>Rules come from a supplied ATS configuration export; this is not a live ATS audit.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Pool records did not apply to this requisition. Their results are hypothetical: they show how the supplied rule would treat them, not an exclusion that happened.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q5, knowledge:skill.terraform. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.terraform.</sub>

Decision: **deferred** by recruiter.lee@northwind.example (2026-10-12T15:20:00Z): Superseded by the broader Q5 change; revisit if Q5 stays literal.

### Business necessity of required qualification R6 is undocumented

`SA-REQ-SRE-0142-ff4b8adc` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `unverified_necessity`

R6 ('Experience in the logistics or freight industry.') is marked required, but has no documented rationale and is not linked to any stated job objective.

**Evidence**
- `requirement:R6` — Experience in the logistics or freight industry.

**Proposed action:** Classify the requirement: essential (document the rationale), preferred, or demonstrable through alternatives.

**Expected benefit:** Required qualifications reflect what the job actually needs, and the rationale is auditable.  
**Trade-off:** Requires a short hiring-manager conversation.

**Limitations**
- The requirement may be genuinely necessary; this finding asks for clarification, not removal.

**Screening-risk category:** Insufficient evidence or unknown cause

**Correction simulation:** not evaluated — No configuration correction is proposed: this finding asks the employer to classify the requirement. Its effect appears after a recorded decision and a re-run.

<sub>Sources: requirement:R6. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **reclassified_preferred** by hm.okafor@northwind.example (2026-10-12T16:12:00Z): Freight experience helps but is not needed to do the job.

### 2 exclusion(s) are not explained by the supplied screening rules

`SA-REQ-SRE-0142-0b941a58` · Level 2 · Plausible missed-talent risk · confidence **high** · check `unexplained_exclusions`

Candidates C-113, C-114 were rejected or deprioritized, but pass every supplied rule. Either the supplied configuration is incomplete, or the exclusions were manual decisions.

**Evidence**
- `candidate:C-113` — no supplied rule fails
- `candidate:C-114` — no supplied rule fails; cannot be evaluated: Q3 (no recorded answer)

**Consequence in the supplied candidate sample:** 2 candidate(s) would pass this rule under this correction alone (C-113, C-114); 0 candidate-review opportunities depend on it.

**Proposed action:** Supply the complete ATS screening configuration, or confirm these were manual decisions.

**Expected benefit:** A complete audit, and visibility into undocumented screening criteria.  
**Trade-off:** None.

**Limitations**
- The engine can only audit configuration it was given; it does not claim a complete audit.

**Screening-risk category:** Insufficient evidence or unknown cause

**Correction simulation:** not evaluated — The supplied rules do not establish why these candidates were excluded, so no correction can be simulated. Treat as unknown, not as missed candidates.

<sub>Sources: candidate:C-113, candidate:C-114. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **requested_evidence** by recruiter.lee@northwind.example (2026-10-12T15:25:00Z): Asked the ATS admin for the full configuration export; C-113 may have been a manual rejection.

## 5. Candidate-review opportunities

### Candidate C-102 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-5f56524c` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-102 was rejected by Q1, Q2, Q5. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (64 mo) | different terminology | `experience[0].title` Production Reliability Engineer |
| R2 | required | Evidenced | different terminology | `experience[0].s2` Led incident response for major outages and coordinated restoration across teams. |
| R3 | required | Evidenced | equivalent tool / credential | `experience[0].s4` Provisioned infrastructure with Pulumi and automated deployments.<br>`skills.s1` Pulumi. |
| R4 | preferred | Evidenced | same terminology | `skills.s2` Kubernetes. |
| R5 | preferred | Evidenced | different terminology | `education.s1` BS in Computer Science |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q1 — no listed term found; Q2 — 0 relevant months vs 84 required; Q5 — no listed term found

**How their path differs from the conventional one**
- R1 described in different terminology: production reliability engineer
- R2 described in different terminology: incident response
- R3 evidenced through an equivalent tool or skill: Pulumi
- R5 described in different terminology: BS in computer science
- Experience domains: e-commerce

**What remains unproven**
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Terminology not recognized

<sub>Sources: candidate:C-102, rule:Q1, rule:Q2, rule:Q5. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **approved_candidate_review** by recruiter.lee@northwind.example (2026-10-12T15:30:00Z): Production reliability engineer title; review.

### Candidate C-103 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-4989b969` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `candidate_review_opportunity`

C-103 was rejected by Q1, Q2, Q3, Q4, Q6, Q7. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (66 mo) | different terminology | `experience[0].title` Clinical Systems Operations Manager<br>`experience[0].s1` Ran systems operations for the electronic health record platform across four hospitals, owning uptime and availability of production systems. |
| R2 | required | Evidenced via alternative path | transferable experience (eq.incident-management.operational-crisis-response) | `experience[0].s2` Led the response to EHR outages and coordinated restoration across clinical and IT teams.<br>`experience[0].s4` Ran post-incident reviews that produced corrective actions. |
| R3 | required | Evidenced | same terminology, equivalent tool / credential | `experience[0].s5` Automated server provisioning with Terraform and Ansible.<br>`experience[0].s5` Automated server provisioning with Terraform and Ansible. |
| R4 | preferred | Not evidenced | — | — |
| R5 | preferred | Not evidenced | — | — |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q1 — no listed term found; Q2 — 0 relevant months vs 84 required; Q3 — answered 'no', rule requires 'yes'; Q4 — answered 'no', rule requires 'yes'; Q6 — answered 'no', rule requires 'yes'; Q7 — no listed term found

**How their path differs from the conventional one**
- R1 described in different terminology: systems operations
- R2 evidenced through transferable experience (eq.incident-management.operational-crisis-response)
- R3 evidenced through an equivalent tool or skill: Ansible
- Experience domains: healthcare-operations

**What remains unproven**
- R2: eq.incident-management.operational-crisis-response: 4 of 4 indicators present; 66 months of relevant experience. Conditions: Evidence must show the candidate led or coordinated response, not merely participated in an event. Responsibilities must be comparable in complexity (multiple teams, time-critical restoration). At least three of the four indicators must be present, including leadership of the response.
- R4: Not evidenced
- R5: Not evidenced
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Ask for a specific incident the candidate led, its scale, and their decision-making role.
- Confirm they communicated status to stakeholders during the event.
- Confirm they drove a review that produced corrective actions.
- Assess ability to learn the employer's production stack (technical depth is a separate requirement).

**Screening-risk category:** Potentially equivalent experience

<sub>Sources: candidate:C-103, rule:Q1, rule:Q2, rule:Q3, rule:Q4, rule:Q6, rule:Q7. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.incident-management.operational-crisis-response.</sub>

Decision: **approved_candidate_review** by recruiter.lee@northwind.example (2026-10-12T15:31:00Z): Hospital EHR incident lead; verify Terraform depth.

### Candidate C-106 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-36d39631` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `candidate_review_opportunity`

C-106 was rejected by Q1, Q2, Q3, Q4, Q6, Q7. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (72 mo) | different terminology | `experience[0].s1` Directed network and infrastructure operations for a 2,000-person brigade. |
| R2 | required | Evidenced via alternative path | transferable experience (eq.incident-management.operational-crisis-response) | `experience[0].s2` Directed the response to communications outages during deployments, restoring service across units.<br>`experience[0].s2` Directed the response to communications outages during deployments, restoring service across units. |
| R3 | required | Evidenced | same terminology, equivalent tool / credential, different terminology | `experience[0].s5` Built infrastructure automation with Ansible and Terraform.<br>`experience[0].s5` Built infrastructure automation with Ansible and Terraform. |
| R4 | preferred | Evidenced | same terminology | `learning.s1` Self-directed study of Kubernetes |
| R5 | preferred | Not evidenced | — | — |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q1 — no listed term found; Q2 — 0 relevant months vs 84 required; Q3 — answered 'no', rule requires 'yes'; Q4 — answered 'no', rule requires 'yes'; Q6 — answered 'no', rule requires 'yes'; Q7 — no listed term found

**How their path differs from the conventional one**
- R1 described in different terminology: infrastructure operations
- R2 evidenced through transferable experience (eq.incident-management.operational-crisis-response)
- R3 evidenced through an equivalent tool or skill: Ansible
- R3 described in different terminology: infrastructure automation
- Experience domains: military

**What remains unproven**
- R2: eq.incident-management.operational-crisis-response: 4 of 4 indicators present; 72 months of relevant experience. Conditions: Evidence must show the candidate led or coordinated response, not merely participated in an event. Responsibilities must be comparable in complexity (multiple teams, time-critical restoration). At least three of the four indicators must be present, including leadership of the response.
- R5: Not evidenced
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Ask for a specific incident the candidate led, its scale, and their decision-making role.
- Confirm they communicated status to stakeholders during the event.
- Confirm they drove a review that produced corrective actions.
- Assess ability to learn the employer's production stack (technical depth is a separate requirement).

**Screening-risk category:** Potentially equivalent experience

<sub>Sources: candidate:C-106, rule:Q1, rule:Q2, rule:Q3, rule:Q4, rule:Q6, rule:Q7. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.incident-management.operational-crisis-response.</sub>

Decision: **approved_candidate_review** by recruiter.lee@northwind.example (2026-10-12T15:32:00Z): Military communications operations; verify production-scale automation.

### Candidate C-108 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-cd635676` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-108 was rejected by Q2, Q4. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (72 mo) | same terminology | `experience[0].title` Site Reliability Engineer |
| R2 | required | Evidenced | different terminology | `experience[0].s1` Led incident response as incident commander for trading systems. |
| R3 | required | Evidenced | same terminology | `experience[0].s3` Managed Terraform and Kubernetes for production infrastructure.<br>`skills.s1` Terraform. |
| R4 | preferred | Evidenced | same terminology | `experience[0].s3` Managed Terraform and Kubernetes for production infrastructure.<br>`skills.s2` Kubernetes. |
| R5 | preferred | Not evidenced | — | — |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q2 — 72 relevant months vs 84 required; Q4 — answered 'no', rule requires 'yes'

**How their path differs from the conventional one**
- R2 described in different terminology: incident response
- Experience domains: fintech

**What remains unproven**
- R5: Not evidenced
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Preferred criterion enforced as a knockout

<sub>Sources: candidate:C-108, rule:Q2, rule:Q4. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **approved_candidate_review** by recruiter.lee@northwind.example (2026-10-12T15:33:00Z): Conventional profile without a degree.

### Candidate C-109 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-c1d0ef0b` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-109 was rejected by Q2, Q6. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (66 mo) | same terminology | `experience[0].title` Site Reliability Engineer |
| R2 | required | Evidenced | different terminology | `experience[0].s2` Led incident response for customer-facing outages and wrote postmortems. |
| R3 | required | Evidenced | same terminology | `experience[0].s3` Maintained Terraform for all infrastructure.<br>`skills.s2` Terraform. |
| R4 | preferred | Not evidenced | — | — |
| R5 | preferred | Evidenced | different terminology | `education.s1` BS in Computer Science |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q2 — 66 relevant months vs 84 required; Q6 — answered 'no', rule requires 'yes'

**How their path differs from the conventional one**
- R2 described in different terminology: incident response
- R5 described in different terminology: BS in computer science
- Experience domains: media

**What remains unproven**
- R4: Not evidenced
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Preferred criterion enforced as a knockout

<sub>Sources: candidate:C-109, rule:Q2, rule:Q6. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **approved_candidate_review** by recruiter.lee@northwind.example (2026-10-12T15:34:00Z): Nomad instead of Kubernetes.

### Candidate C-110 may meet the requirements through a path the current rules do not recognize

`SA-REQ-SRE-0142-82276566` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-110 was rejected by Q1, Q2, Q7. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (74 mo) | different terminology | `experience[0].s1` Owned production infrastructure operations and on-call for a SaaS platform. |
| R2 | required | Evidenced | different terminology | `experience[0].s2` Led incident response for major outages and authored postmortems. |
| R3 | required | Evidenced | same terminology, equivalent tool / credential | `experience[0].s3` Wrote Terraform and CloudFormation for all environments.<br>`experience[0].s3` Wrote Terraform and CloudFormation for all environments. |
| R4 | preferred | Evidenced | same terminology | `skills.s3` Kubernetes. |
| R5 | preferred | Evidenced | different terminology | `education.s1` BS in Computer Science |
| R6 | preferred | Not evidenced | — | — |

**Excluded by:** Q1 — no listed term found; Q2 — 0 relevant months vs 84 required; Q7 — no listed term found

**How their path differs from the conventional one**
- R1 described in different terminology: infrastructure operations
- R2 described in different terminology: incident response
- R3 evidenced through an equivalent tool or skill: CloudFormation
- R5 described in different terminology: BS in computer science
- Experience domains: saas

**What remains unproven**
- R6: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Rule narrower than the requirement

<sub>Sources: candidate:C-110, rule:Q1, rule:Q2, rule:Q7. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

## 6. Recommended changes

Suggested configuration changes, for the employer to implement in the ATS. Nothing is applied automatically.

**Q1** — Résumé must mention site reliability engineer or SRE.  
Proposed by: `SA-REQ-SRE-0142-704c5892` (accepted), `SA-REQ-SRE-0142-9164e1d0` (accepted), `SA-REQ-SRE-0142-b05a4c5a` (accepted)

```yaml
suggested_logic:
  terms:
  - site reliability engineer
  - SRE
  - Site reliability engineering
  - production reliability engineering
  - production reliability engineer
  - Production operations
  - IT operations
  - systems operations
  - infrastructure operations
  - operations engineering
  - platform operations
  - network operations
  match: any
  field: resume
  allows_equivalent: true
  equivalencies:
  - eq.site-reliability.production-operations
```

**Q2** — At least 7 years in Site Reliability Engineer roles (by job title).  
Proposed by: `SA-REQ-SRE-0142-9403725f` (accepted), `SA-REQ-SRE-0142-d15dcf14` (accepted), `SA-REQ-SRE-0142-e3e3d885` (rejected), `SA-REQ-SRE-0142-a0ac83a9` (accepted)

```yaml
suggested_logic:
  terms:
  - site reliability engineer
  - SRE
  - Production operations
  - IT operations
  - systems operations
  - infrastructure operations
  - operations engineering
  - platform operations
  - network operations
  - Site reliability engineering
  - production reliability engineering
  - production reliability engineer
  years: 5
  field: resume
  equivalencies:
  - eq.site-reliability.production-operations
```

**Q3** — Have you served as incident commander for a software production environment?  
Proposed by: `SA-REQ-SRE-0142-5302d6be` (accepted)

```yaml
suggested_logic:
  required_answer: 'yes'
  allows_equivalent: true
  equivalencies:
  - eq.incident-management.operational-crisis-response
  evidence_concepts:
  - skill.incident-management
```

**Q4** — Do you hold a bachelor's degree in computer science?  
Proposed by: `SA-REQ-SRE-0142-3bc61a83` (accepted), `SA-REQ-SRE-0142-512cd6d3` (accepted)

```yaml
suggested_logic:
  removed: true
```

**Q5** — Résumé must mention Terraform.  
Proposed by: `SA-REQ-SRE-0142-f01e2bd0` (accepted), `SA-REQ-SRE-0142-9d626aeb` (deferred)

```yaml
suggested_logic:
  terms:
  - Terraform
  - HashiCorp Terraform
  - OpenTofu
  - Infrastructure as code
  - infrastructure automation
  - IaC
  - Ansible
  - AWS CloudFormation
  - CloudFormation
  - Pulumi
  match: any
  field: resume
```

**Q6** — Do you have hands-on Kubernetes experience?  
Proposed by: `SA-REQ-SRE-0142-48360a3a` (accepted)

```yaml
suggested_logic:
  removed: true
```

**Q7** — Résumé must mention Datadog.  
Proposed by: `SA-REQ-SRE-0142-99df8968` (accepted)

```yaml
suggested_logic:
  removed: true
```

## 7. Human decisions and rationale

| Finding | Decision | By | Rationale |
|---|---|---|---|
| `SA-REQ-SRE-0142-704c5892` R1 accepts equivalent experience, but Q1 has no equivalent path | accepted | recruiter.lee@northwind.example | Posting already accepts equivalent experience; add a recruiter-review route for production-operations résumés. |
| `SA-REQ-SRE-0142-9164e1d0` Q1 is narrower than R1: it ignores Production operations | accepted | recruiter.lee@northwind.example | R1 explicitly allows production operations; the filter should too. |
| `SA-REQ-SRE-0142-9403725f` Q2 is narrower than R1: it ignores Production operations | accepted | recruiter.lee@northwind.example | Consistent with R1. |
| `SA-REQ-SRE-0142-d15dcf14` Q2 requires 7 years; the posting asks for 5 | accepted | hm.okafor@northwind.example | Five years is the real bar; seven was copied from the staff-level req. |
| `SA-REQ-SRE-0142-5302d6be` R2 accepts equivalent experience, but Q3 has no equivalent path | accepted | hm.okafor@northwind.example | Some of our best incident leads came from operations. Route 'no' answers with crisis-leadership evidence to review. |
| `SA-REQ-SRE-0142-3bc61a83` Preferred qualification R5 is enforced as a knockout by Q4 | accepted | hm.okafor@northwind.example | Degree is a preference; use it for ranking only. |
| `SA-REQ-SRE-0142-512cd6d3` R5 accepts equivalent experience, but Q4 has no equivalent path | accepted | hm.okafor@northwind.example | Same change as the knockout removal. |
| `SA-REQ-SRE-0142-f01e2bd0` Q5 is narrower than R3: it ignores Infrastructure as code | accepted | hm.okafor@northwind.example | Pulumi, CloudFormation and Ansible experience transfers; we said 'or equivalent'. |
| `SA-REQ-SRE-0142-48360a3a` Preferred qualification R4 is enforced as a knockout by Q6 | accepted | hm.okafor@northwind.example | Kubernetes is learnable; Nomad experience is fine. |
| `SA-REQ-SRE-0142-99df8968` Rule Q7 enforces a requirement the job description does not state | accepted | hm.okafor@northwind.example | Stale filter from an earlier requisition; we run Prometheus and any monitoring experience transfers. |
| `SA-REQ-SRE-0142-b05a4c5a` Q1 matches literally and misses recognized variants of Site reliability engineering | accepted | recruiter.lee@northwind.example | Same function, different title. |
| `SA-REQ-SRE-0142-e3e3d885` Q2 matches literally and misses recognized variants of Site reliability engineering | rejected | recruiter.lee@northwind.example | Moot: Q2 will count responsibilities across the résumé (see the experience-path finding), so adding title variants is unnecessary. |
| `SA-REQ-SRE-0142-a0ac83a9` Q2 counts experience only under specific job titles | accepted | hm.okafor@northwind.example | Count responsibilities, not titles; recruiter verifies scope. |
| `SA-REQ-SRE-0142-9d626aeb` Q5 matches literally and misses recognized variants of Terraform | deferred | recruiter.lee@northwind.example | Superseded by the broader Q5 change; revisit if Q5 stays literal. |
| `SA-REQ-SRE-0142-ff4b8adc` Business necessity of required qualification R6 is undocumented | reclassified_preferred | hm.okafor@northwind.example | Freight experience helps but is not needed to do the job. |
| `SA-REQ-SRE-0142-5f56524c` Candidate C-102 may meet the requirements through a path the current rules do not recognize | approved_candidate_review | recruiter.lee@northwind.example | Production reliability engineer title; review. |
| `SA-REQ-SRE-0142-4989b969` Candidate C-103 may meet the requirements through a path the current rules do not recognize | approved_candidate_review | recruiter.lee@northwind.example | Hospital EHR incident lead; verify Terraform depth. |
| `SA-REQ-SRE-0142-36d39631` Candidate C-106 may meet the requirements through a path the current rules do not recognize | approved_candidate_review | recruiter.lee@northwind.example | Military communications operations; verify production-scale automation. |
| `SA-REQ-SRE-0142-cd635676` Candidate C-108 may meet the requirements through a path the current rules do not recognize | approved_candidate_review | recruiter.lee@northwind.example | Conventional profile without a degree. |
| `SA-REQ-SRE-0142-c1d0ef0b` Candidate C-109 may meet the requirements through a path the current rules do not recognize | approved_candidate_review | recruiter.lee@northwind.example | Nomad instead of Kubernetes. |
| `SA-REQ-SRE-0142-0b941a58` 2 exclusion(s) are not explained by the supplied screening rules | requested_evidence | recruiter.lee@northwind.example | Asked the ATS admin for the full configuration export; C-113 may have been a manual rejection. |

## 8. Outcome measurements

Comparison method: **Pre/post on the same requisition: three weeks before the corrections versus three weeks after. Recruiter time from the ATS activity log. Not a controlled experiment.**

**Measured**

| Metric | Value |
|---|---|
| Additional candidates receiving human review | 5 |
| Confirmed to meet requirements | 4 |
| Confirmed not to meet requirements (false positives) | 0 |
| Insufficient evidence | 1 |
| Advanced to next stage | 4 |
| Recruiter minutes spent on additional review | 85 |
| Share of additional reviews confirmed qualified | 0.8 |
| Incremental qualified candidates per recruiter hour | 2.824 |

| Period metric | Baseline | After change | Δ |
|---|---|---|---|
| applicants | 142 | 61 | — |
| recruiter reviewed | 18 | 15 | -3 |
| qualified candidates | 3 | 5 | 2 |
| recruiter hours | 14 | 11 | -3 |
| qualified yield | 0.167 | 0.333 | 0.166 |
| recruiter hours per qualified | 4.667 | 2.2 | -2.467 |
| days to qualified shortlist | 21 | 9 | -12 |

**ESTIMATED — based on supplied assumptions, not observed**

- additional review cost: 77.92
- sourcing cycles potentially avoided: 1.33
- sourcing cost potentially avoided: 8666.67
- net estimated value: 8588.75
- assumptions: {'cost_per_sourcing_cycle': 6500, 'qualified_candidates_needed_per_cycle': 3, 'recruiter_hourly_cost': 55, 'source': 'Northwind TA finance planning assumptions (illustrative)'}

**Attribution: which corrections the reviewed candidates depended on**

| Finding | Reviewed | Met requirements | Minutes |
|---|---|---|---|
| `SA-REQ-SRE-0142-d15dcf14` Q2 requires 7 years; the posting asks for 5 | 5 | 4 | 85 |
| `SA-REQ-SRE-0142-3bc61a83` Preferred qualification R5 is enforced as a knockout by Q4 | 3 | 2 | 60 |
| `SA-REQ-SRE-0142-48360a3a` Preferred qualification R4 is enforced as a knockout by Q6 | 3 | 2 | 60 |
| `SA-REQ-SRE-0142-512cd6d3` R5 accepts equivalent experience, but Q4 has no equivalent path | 3 | 2 | 60 |
| `SA-REQ-SRE-0142-704c5892` R1 accepts equivalent experience, but Q1 has no equivalent path | 2 | 2 | 40 |
| `SA-REQ-SRE-0142-9403725f` Q2 is narrower than R1: it ignores Production operations | 3 | 2 | 65 |
| `SA-REQ-SRE-0142-a0ac83a9` Q2 counts experience only under specific job titles | 3 | 2 | 65 |
| `SA-REQ-SRE-0142-5302d6be` R2 accepts equivalent experience, but Q3 has no equivalent path | 2 | 1 | 50 |
| `SA-REQ-SRE-0142-9164e1d0` Q1 is narrower than R1: it ignores Production operations | 2 | 1 | 50 |
| `SA-REQ-SRE-0142-99df8968` Rule Q7 enforces a requirement the job description does not state | 2 | 1 | 50 |
| `SA-REQ-SRE-0142-b05a4c5a` Q1 matches literally and misses recognized variants of Site reliability engineering | 1 | 1 | 15 |
| `SA-REQ-SRE-0142-f01e2bd0` Q5 is narrower than R3: it ignores Infrastructure as code | 1 | 1 | 15 |

**New risks observed**
- Broader Q1 matching admitted 4 additional applicants who were screened out in about 20 recruiter minutes in total.

_Measured values come from recorded recruiter reviews and supplied period data. Changes between periods are associated with, not proven to be caused by, approved corrections unless the comparison method controls for other factors._

### Measured: 4 of 5 additionally reviewed candidates met the role's requirements

`SA-REQ-SRE-0142-28d82855` · Level 3 · Measured impact · confidence **high** · check `measured_impact`

After human review, 4 of 5 candidate(s) surfaced by this analysis were confirmed to meet the role's requirements (0 did not, 1 had insufficient evidence), using 85 recruiter minutes — 2.824 incremental qualified candidates per recruiter hour.

**Evidence**
- `outcome:C-102` — meets_requirements after 15 min; advanced to phone_screen
- `outcome:C-103` — meets_requirements after 25 min; advanced to hiring_manager_screen
- `outcome:C-106` — insufficient_evidence after 25 min
- `outcome:C-108` — meets_requirements after 10 min; advanced to phone_screen
- `outcome:C-109` — meets_requirements after 10 min; advanced to phone_screen

**Proposed action:** Keep the corrections whose candidates were confirmed; submit confirmed equivalencies as knowledge proposals.

**Expected benefit:** 4 confirmed qualified candidate(s) recovered from the existing applicant pool.  
**Trade-off:** 85 recruiter minutes; 1 reviewed candidate(s) not (yet) confirmed.

**Limitations**
- Pre/post on the same requisition: three weeks before the corrections versus three weeks after. Recruiter time from the ATS activity log. Not a controlled experiment.
- Small sample; confirm across more requisitions before generalizing.

<sub>Sources: outcome:C-102, outcome:C-103, outcome:C-106, outcome:C-108, outcome:C-109. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: _No decision required (measured outcome)._

## Appendix A — Candidates assessed but not surfaced

| Candidate | ATS status | Excluded by | Reason |
|---|---|---|---|
| C-101 | advanced | — | Not excluded by the ATS (status: advanced). |
| C-104 | rejected | Q1, Q2, Q3, Q4, Q5, Q6, Q7 | Still excluded after proposed corrections by Q5. |
| C-105 | rejected | Q1, Q2, Q3, Q4, Q5, Q6, Q7 | Still excluded after proposed corrections by Q1, Q2, Q3, Q5. |
| C-107 | rejected | Q2, Q3 | Still excluded after proposed corrections by Q2. |
| C-111 | rejected | Q1, Q2, Q3, Q4, Q5, Q6, Q7 | Still excluded after proposed corrections by Q2, Q3, Q5. |
| C-112 | rejected | Q1, Q2, Q3, Q5, Q6, Q7 | Still excluded after proposed corrections by Q1, Q2, Q3, Q5. |
| C-113 | rejected | — | Excluded, but the supplied rules do not explain the exclusion. |
| C-114 | rejected | — | Excluded, but the supplied rules do not explain the exclusion. |
