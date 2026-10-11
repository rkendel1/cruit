# Requisition assurance report — Customer Success Manager, Mid-Market (REQ-CSM-0388)

Job family `customer-success` · employer `northwind` · knowledge `core@1.1.0+8a94e741e4` (approved) · engine 0.2.0 · run 2026-11-03T12:00:00Z

> This report recommends changes and human review. It does not reject, advance or hire anyone, and it does not claim any candidate was wrongly excluded. Level 1 findings are established by the supplied materials; Level 2 findings are risks that need human judgement; Level 3 findings are measured outcomes.

## Summary

- **3** demonstrable inconsistencies (Level 1)
- **8** missed-talent risks and review opportunities (Level 2), including **3** candidate(s) of 8 assessed surfaced for human review
- **0** measured outcomes (Level 3)
- **7** findings awaiting a human decision

**Inputs received:** job description: `supplied`, screening configuration: `recruiter_documentation`, candidate evidence: `authorized_sample`

**Limitations of this run**
- Requirement R4 treated as 'preferred' because of human decision on SA-REQ-CSM-0388-a1beef17.
- Screening rules were supplied as recruiter documentation, not verified ATS configuration. Findings describe the documented rules; the live ATS may differ.
- Candidate evidence is a sample; candidate counts do not represent the full applicant pool.
- Candidate evidence is matched deterministically against the knowledge pack; language-model interpretation is not used in this run.

## 1. Requirements and stated intent

| ID | Requirement | Stated as | Proposed classification | Basis |
|---|---|---|---|---|
| R1 | 3+ years of customer success experience with B2B accounts. | required | Demonstrable through alternatives | posting accepts equivalent experience |
| R2 | Track record of managing renewals for a book of business. | required | Essential | linked to objectives ['O1'] |
| R3 | Data-driven approach to account health. | preferred | Preferred | stated as preferred in the posting |
| R4 | Salesforce proficiency. | preferred | Preferred | set by recorded human decision |
| R5 | Cross-functional problem-solving with product and support teams. | required | Demonstrable through alternatives | posting accepts equivalent experience |

🔒 = protected (legal, licensing or employer non-negotiable). No alternative path is ever proposed for protected requirements.

## 2. Screening rules inspected

| Rule | Type | Action | Linked requirement | Status | Findings |
|---|---|---|---|---|---|
| Q1 | keyword_filter | reject | R1 | correction proposed | 2 |
| Q2 | title_filter | deprioritize | R1 | correction proposed | 2 |
| Q3 | credential_filter | reject | R4 | correction proposed | 3 |

## 3. Confirmed inconsistencies and protected requirements

### R1 accepts equivalent experience, but Q1 has no equivalent path

`SA-REQ-CSM-0388-7da18d53` · Level 1 · Demonstrable inconsistency · confidence **high** · check `equivalent_path_blocked`

The posting accepts equivalent experience for R1, but rule Q1 only recognizes the listed terms and has no route for recognized equivalent experience.

**Evidence**
- `requirement:R1` — 3+ years of customer success experience with B2B accounts.
- `rule:Q1` — Résumé must mention customer success.

**Proposed action:** Add an equivalent-evidence path (e.g. a follow-up question or recruiter review route) so applicants with equivalent experience are reviewed rather than rejected.

**Expected benefit:** Restores the equivalency the employer already committed to in the posting.  
**Trade-off:** Equivalent-path applicants need recruiter verification time.

**Screening-risk category:** Potentially equivalent experience

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 6: C-202, C-203, C-204, C-205, C-206, C-208 |
| Would pass the proposed rule | 2: C-202, C-204 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 2: C-202, C-204 |

- C-202: eligible together with the proposed corrections to Q2, Q3
- C-204: eligible together with the proposed corrections to Q2, Q3

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R1, rule:Q1. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.customer-success.b2b-account-management.</sub>

Decision: **accepted** by head-of-cs@northwind.example (2026-10-13T14:05:00Z): B2B account managers who own renewals have done well on this team.

### Q3 requires a credential where R4 asks for proficiency

`SA-REQ-CSM-0388-7d038e7c` · Level 1 · Demonstrable inconsistency · confidence **high** · check `credential_stricter_than_requirement`

Requirement R4 asks for a capability ('Salesforce proficiency.'), but rule Q3 requires the credential 'Salesforce Certified Administrator'.

**Evidence**
- `requirement:R4` — Salesforce proficiency.
- `rule:Q3` — Must hold Salesforce Certified Administrator.

**Proposed action:** Accept demonstrated proficiency as well as the credential, or document why the credential itself is required.

**Expected benefit:** Proficient applicants without the specific certification are reviewed.  
**Trade-off:** Proficiency claims need verification during review.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-202, C-203, C-204, C-205, C-206, C-207, C-208 |
| Would pass the proposed rule | 3: C-202, C-204, C-208 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 1: C-208 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 2: C-202, C-204 |

- C-202: eligible together with the proposed corrections to Q1, Q2
- C-204: eligible together with the proposed corrections to Q1, Q2

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R4, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **accepted** by head-of-cs@northwind.example (2026-10-13T14:02:00Z): We never meant to require the admin certification.

### Preferred qualification R4 is enforced as a knockout by Q3

`SA-REQ-CSM-0388-7f815e04` · Level 1 · Demonstrable inconsistency · confidence **high** · check `preferred_enforced_as_knockout`

Requirement R4 is stated as preferred, but rule Q3 rejects applicants who do not meet it.

**Evidence**
- `requirement:R4` — stated_as: preferred — Salesforce proficiency.
- `rule:Q3` — action: reject — Must hold Salesforce Certified Administrator.

**Proposed action:** Convert the rule into a scoring or ranking signal, or reclassify the requirement as essential with a documented rationale.

**Expected benefit:** Applicants who meet all essential requirements are no longer rejected for lacking a preference.  
**Trade-off:** More applicants reach review; ranking should still favour the preferred qualification.

**Screening-risk category:** Preferred criterion enforced as a knockout

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-202, C-203, C-204, C-205, C-206, C-207, C-208 |
| Would pass the proposed rule | 7: C-202, C-203, C-204, C-205, C-206, C-207, C-208 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 4: C-203, C-205, C-206, C-208 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 3: C-202, C-204, C-207 |

- C-202: eligible together with the proposed corrections to Q1, Q2
- C-204: eligible together with the proposed corrections to Q1, Q2
- C-207: eligible this correction alone

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: requirement:R4, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

## 4. Potential missed-talent risks

### Q1 matches literally and misses recognized variants of Customer success

`SA-REQ-CSM-0388-1fa7cee2` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q1 matches only 'customer success'. The knowledge base records 5 equivalent term(s) for Customer success that the rule does not recognize.

**Evidence**
- `knowledge:term.customer-success` — recognized variant(s): client success, customer success management, customer success manager, client success manager, CSM

**Proposed action:** Add recognized variants to the rule: client success, customer success management, customer success manager, client success manager, CSM.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- 'CSM': Also 'Certified ScrumMaster'. Only treated as customer success inside customer-success contexts.
- The presence of a related term does not prove ownership of renewals or account outcomes.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 6: C-202, C-203, C-204, C-205, C-206, C-208 |
| Would pass the proposed rule | 1: C-202 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 1: C-202 |

- C-202: eligible together with the proposed corrections to Q2, Q3

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q1, knowledge:term.customer-success. Knowledge: `core@1.1.0+8a94e741e4`; records: term.customer-success.</sub>

Decision: **accepted** by recruiter.diaz@northwind.example (2026-10-13T13:40:00Z): Client success and customer success are the same job here. Exclude the CSM abbreviation per the ambiguity note.

### Q2 matches literally and misses recognized variants of Customer success

`SA-REQ-CSM-0388-095c74b9` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q2 matches only 'Customer Success Manager'. The knowledge base records 5 equivalent term(s) for Customer success that the rule does not recognize.

**Evidence**
- `knowledge:skill.customer-success` — recognized variant(s): Customer success, client success, customer success management, client success manager, CSM

**Proposed action:** Add recognized variants to the rule: Customer success, client success, customer success management, client success manager, CSM.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- 'CSM': Also 'Certified ScrumMaster'. Only treated as customer success inside customer-success contexts.
- The presence of a related term does not prove ownership of renewals or account outcomes.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 6: C-202, C-203, C-204, C-205, C-206, C-208 |
| Would pass the proposed rule | 1: C-202 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 1: C-202 |

- C-202: eligible together with the proposed corrections to Q1, Q3

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q2, knowledge:skill.customer-success, knowledge:term.customer-success. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.customer-success, term.customer-success.</sub>

Decision: **Pending human decision**

### Q2 counts experience only under specific job titles

`SA-REQ-CSM-0388-309d1f67` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `experience_path_narrower`

Rule Q2 only counts experience held under the titles 'Customer Success Manager'. The underlying capability can be demonstrated under other titles and in other domains.

**Evidence**
- `rule:Q2` — Prioritize applicants who have held the title Customer Success Manager.

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
| Excluded by the supplied rule | 6: C-202, C-203, C-204, C-205, C-206, C-208 |
| Would pass the proposed rule | 2: C-202, C-204 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 2: C-202, C-204 |

- C-202: eligible together with the proposed corrections to Q1, Q3
- C-204: eligible together with the proposed corrections to Q1, Q3

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q2, requirement:R1. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.customer-success.b2b-account-management.</sub>

Decision: **Pending human decision**

### Q3 matches literally and misses recognized variants of Salesforce Certified Administrator

`SA-REQ-CSM-0388-16684b3b` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q3 matches only 'Salesforce Certified Administrator'. The knowledge base records 1 equivalent term(s) for Salesforce Certified Administrator that the rule does not recognize.

**Evidence**
- `knowledge:skill.salesforce-admin-cert` — recognized variant(s): Salesforce Administrator certification

**Proposed action:** Add recognized variants to the rule: Salesforce Administrator certification.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.

**Screening-risk category:** Terminology not recognized

**Correction simulation (not applied)** — supplied rule vs. proposed correction:

| Category | Candidates |
|---|---|
| Excluded by the supplied rule | 7: C-202, C-203, C-204, C-205, C-206, C-207, C-208 |
| Would pass the proposed rule | 0 |
| Still fail a mandatory requirement | 0 |
| Evidence insufficient to tell | 0 |
| Pass the rule, but relevance not established | 0 |
| Relevant evidence, but still fail other supplied rules | 0 |
| Newly eligible for human review | 0 |

<sub>Rules come from recruiter documentation, not ATS configuration; results show the documented rule's effect.</sub>  
<sub>Passing a rule does not mean a candidate is qualified; eligible candidates need human review.</sub>  
<sub>Each correction is simulated on its own. 'Together with the proposed corrections' uses the same combined simulation as candidate-review opportunities, including corrections no human has decided yet.</sub>  

<sub>Sources: rule:Q3, knowledge:skill.salesforce-admin-cert. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.salesforce-admin-cert.</sub>

Decision: **Pending human decision**

### Business necessity of required qualification R4 is undocumented

`SA-REQ-CSM-0388-a1beef17` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `unverified_necessity`

R4 ('Salesforce proficiency.') is marked required, but has no documented rationale and is not linked to any stated job objective.

**Evidence**
- `requirement:R4` — Salesforce proficiency.

**Proposed action:** Classify the requirement: essential (document the rationale), preferred, or demonstrable through alternatives.

**Expected benefit:** Required qualifications reflect what the job actually needs, and the rationale is auditable.  
**Trade-off:** Requires a short hiring-manager conversation.

**Limitations**
- The requirement may be genuinely necessary; this finding asks for clarification, not removal.

**Screening-risk category:** Insufficient evidence or unknown cause

**Correction simulation:** not evaluated — No configuration correction is proposed: this finding asks the employer to classify the requirement. Its effect appears after a recorded decision and a re-run.

<sub>Sources: requirement:R4. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **reclassified_preferred** by head-of-cs@northwind.example (2026-10-13T14:00:00Z): Any modern CRM is fine; Salesforce is learnable in a few weeks.

## 5. Candidate-review opportunities

### Candidate C-202 may meet the requirements through a path the current rules do not recognize

`SA-REQ-CSM-0388-7f33b017` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-202 was rejected by Q1, Q2, Q3. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (50 mo) | different terminology | `experience[0].title` Client Success Lead |
| R2 | required | Evidenced | same terminology | `experience[0].s1` Owned renewals and expansion for a portfolio of 30 enterprise accounts.<br>`experience[0].s4` Maintained pipeline and renewals forecasts in Salesforce. |
| R3 | preferred | Not evidenced | — | — |
| R4 | preferred | Evidenced | same terminology | `experience[0].s4` Maintained pipeline and renewals forecasts in Salesforce. |
| R5 | required | Evidenced | same terminology | `experience[0].s3` Worked cross-functional with product and support teams to resolve blockers. |

**Excluded by:** Q1 — no listed term found; Q2 — no matching title; Q3 — listed credential not held

**How their path differs from the conventional one**
- R1 described in different terminology: client success
- Experience domains: saas

**What remains unproven**
- R3: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Terminology not recognized

<sub>Sources: candidate:C-202, rule:Q1, rule:Q2, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

### Candidate C-204 may meet the requirements through a path the current rules do not recognize

`SA-REQ-CSM-0388-dc08d1e4` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `candidate_review_opportunity`

C-204 was rejected by Q1, Q2, Q3. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced via alternative path (52 mo) | transferable experience (eq.customer-success.b2b-account-management) | `experience[0].s1` Managed a book of 40 mid-market SaaS accounts.<br>`experience[0].s2` Owned renewals and grew revenue through expansion across accounts. |
| R2 | required | Evidenced | same terminology | `experience[0].s2` Owned renewals and grew revenue through expansion across accounts.<br>`experience[0].s5` Tracked pipeline and renewals in Salesforce. |
| R3 | preferred | Not evidenced | — | — |
| R4 | preferred | Evidenced | same terminology | `experience[0].s5` Tracked pipeline and renewals in Salesforce. |
| R5 | required | Evidenced | same terminology | `experience[0].s4` Coordinated cross-functional fixes with product and support teams. |

**Excluded by:** Q1 — no listed term found; Q2 — no matching title; Q3 — listed credential not held

**How their path differs from the conventional one**
- R1 evidenced through transferable experience (eq.customer-success.b2b-account-management)
- Experience domains: saas

**What remains unproven**
- R1: eq.customer-success.b2b-account-management: 4 of 4 indicators present; 52 months of relevant experience. Conditions: Candidate must have owned renewals, not only new-business sales. Accounts must be business customers with recurring contracts.
- R3: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm size and segment of the book of business.
- Confirm renewal ownership and retention results.
- Confirm adoption or onboarding work, not only commercial negotiation.

**Screening-risk category:** Potentially equivalent experience

<sub>Sources: candidate:C-204, rule:Q1, rule:Q2, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.customer-success.b2b-account-management.</sub>

Decision: **Pending human decision**

### Candidate C-207 may meet the requirements through a path the current rules do not recognize

`SA-REQ-CSM-0388-ea6778d8` · Level 2 · Plausible missed-talent risk · confidence **high** · check `candidate_review_opportunity`

C-207 was rejected by Q3. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced (44 mo) | same terminology | `experience[0].title` Customer Success Manager |
| R2 | required | Evidenced | same terminology | `experience[0].s1` Owned renewals for a book of 35 SMB SaaS accounts. |
| R3 | preferred | Not evidenced | — | — |
| R4 | preferred | Not evidenced | — | — |
| R5 | required | Evidenced | same terminology | `experience[0].s3` Worked cross-functional with product and support to unblock customers. |

**Excluded by:** Q3 — listed credential not held

**How their path differs from the conventional one**
- Experience domains: saas

**What remains unproven**
- R3: Not evidenced
- R4: Not evidenced
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm the depth and recency of the experience cited for each required requirement.

**Screening-risk category:** Preferred criterion enforced as a knockout

<sub>Sources: candidate:C-207, rule:Q3. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

## 6. Recommended changes

Suggested configuration changes, for the employer to implement in the ATS. Nothing is applied automatically.

**Q1** — Résumé must mention customer success.  
Proposed by: `SA-REQ-CSM-0388-7da18d53` (accepted), `SA-REQ-CSM-0388-1fa7cee2` (accepted)

```yaml
suggested_logic:
  terms:
  - customer success
  - client success
  - customer success management
  - customer success manager
  - client success manager
  - CSM
  match: any
  field: resume
  allows_equivalent: true
  equivalencies:
  - eq.customer-success.b2b-account-management
```

**Q2** — Prioritize applicants who have held the title Customer Success Manager.  
Proposed by: `SA-REQ-CSM-0388-095c74b9` (pending), `SA-REQ-CSM-0388-309d1f67` (pending)

```yaml
suggested_logic:
  terms:
  - Customer Success Manager
  - Customer success
  - client success
  - customer success management
  - client success manager
  - CSM
  field: resume
  equivalencies:
  - eq.customer-success.b2b-account-management
```

**Q3** — Must hold Salesforce Certified Administrator.  
Proposed by: `SA-REQ-CSM-0388-7d038e7c` (accepted), `SA-REQ-CSM-0388-7f815e04` (pending), `SA-REQ-CSM-0388-16684b3b` (pending)

```yaml
suggested_logic:
  removed: true
```

## 7. Human decisions and rationale

| Finding | Decision | By | Rationale |
|---|---|---|---|
| `SA-REQ-CSM-0388-7da18d53` R1 accepts equivalent experience, but Q1 has no equivalent path | accepted | head-of-cs@northwind.example | B2B account managers who own renewals have done well on this team. |
| `SA-REQ-CSM-0388-7d038e7c` Q3 requires a credential where R4 asks for proficiency | accepted | head-of-cs@northwind.example | We never meant to require the admin certification. |
| `SA-REQ-CSM-0388-1fa7cee2` Q1 matches literally and misses recognized variants of Customer success | accepted | recruiter.diaz@northwind.example | Client success and customer success are the same job here. Exclude the CSM abbreviation per the ambiguity note. |
| `SA-REQ-CSM-0388-a1beef17` Business necessity of required qualification R4 is undocumented | reclassified_preferred | head-of-cs@northwind.example | Any modern CRM is fine; Salesforce is learnable in a few weeks. |

## 8. Outcome measurements

_No outcome data supplied yet. Add `outcomes.yaml` with a documented baseline after corrections are implemented._

## Appendix A — Candidates assessed but not surfaced

| Candidate | ATS status | Excluded by | Reason |
|---|---|---|---|
| C-201 | advanced | — | Not excluded by the ATS (status: advanced). |
| C-203 | rejected | Q1, Q2, Q3 | Still excluded after proposed corrections by Q1, Q2. |
| C-205 | rejected | Q1, Q2, Q3 | Still excluded after proposed corrections by Q1, Q2. |
| C-206 | rejected | Q1, Q2, Q3 | Still excluded after proposed corrections by Q1, Q2. |
| C-208 | rejected | Q1, Q2, Q3 | Still excluded after proposed corrections by Q1, Q2. |

## Appendix B — Protected and suppressed items

- equivalency `eq.customer-success.support-escalation-leadership` (rule Q2): rejected by employer policy (head-of-cs@northwind.example): Our CSM roles carry full commercial quota; support escalation alone has not predicted success here.
