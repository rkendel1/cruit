# Requisition assurance report — Linehaul Operations Supervisor (REQ-LH-0217)

Job family `logistics-operations` · employer `northwind` · knowledge `core@1.1.0+8a94e741e4` (approved) · engine 0.1.0 · run 2026-11-03T12:00:00Z

> This report recommends changes and human review. It does not reject, advance or hire anyone, and it does not claim any candidate was wrongly excluded. Level 1 findings are established by the supplied materials; Level 2 findings are risks that need human judgement; Level 3 findings are measured outcomes.

## Summary

- **0** demonstrable inconsistencies (Level 1)
- **4** missed-talent risks and review opportunities (Level 2), including **1** candidate(s) of 4 assessed surfaced for human review
- **0** measured outcomes (Level 3)
- **4** findings awaiting a human decision

**Inputs received:** job description: `supplied`, screening configuration: `ats_export_verified`, candidate evidence: `authorized_sample`

**Limitations of this run**
- Candidate evidence is a sample; candidate counts do not represent the full applicant pool.
- Candidate evidence is matched deterministically against the knowledge pack; language-model interpretation is not used in this run.

## 1. Requirements and stated intent

| ID | Requirement | Stated as | Proposed classification | Basis |
|---|---|---|---|---|
| R1 | Active Class A commercial driver's license. | required | Essential 🔒 | Commercial driver's license (Class A) is a regulated credential in the knowledge base |
| R2 | 3+ years supervising transportation or dispatch operations. | required | Demonstrable through alternatives | posting accepts equivalent experience |
| R3 | Working knowledge of DOT and hours-of-service compliance. | required | Essential | linked to objectives ['O2'] |

🔒 = protected (legal, licensing or employer non-negotiable). No alternative path is ever proposed for protected requirements.

## 2. Screening rules inspected

| Rule | Type | Action | Linked requirement | Status | Findings |
|---|---|---|---|---|---|
| Q1 | credential_filter | reject | R1 | protected | 1 |
| Q2 | minimum_experience | reject | R2 | correction proposed | 2 |

## 3. Confirmed inconsistencies

_None found._

## 4. Potential missed-talent risks

### Q1 matches literally and misses recognized variants of Commercial driver's license (Class A)

`SA-REQ-LH-0217-24c327f3` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q1 matches only 'CDL Class A'. The knowledge base records 5 equivalent term(s) for Commercial driver's license (Class A) that the rule does not recognize.

**Evidence**
- `knowledge:skill.cdl-class-a` — recognized variant(s): Commercial driver's license (Class A), Class A CDL, CDL-A, Class A commercial driver's license, commercial driver license class A

**Consequence in the supplied candidate sample:** 1 candidate(s) would pass this rule under this correction alone (C-303); 1 candidate-review opportunity depends on it (C-303).

**Proposed action:** Add recognized variants to the rule: Commercial driver's license (Class A), Class A CDL, CDL-A, Class A commercial driver's license, commercial driver license class A.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- Terminology only. A license is never satisfied by adjacent experience.

<sub>Sources: rule:Q1, knowledge:skill.cdl-class-a, knowledge:term.cdl-class-a. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.cdl-class-a, term.cdl-class-a.</sub>

Decision: **Pending human decision**

### Q2 matches literally and misses recognized variants of Transportation supervision

`SA-REQ-LH-0217-bdfae568` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q2 matches only 'Transportation Supervisor', 'Dispatch Supervisor'. The knowledge base records 4 equivalent term(s) for Transportation supervision that the rule does not recognize.

**Evidence**
- `knowledge:skill.transportation-supervision` — recognized variant(s): Transportation supervision, dispatch supervision, fleet supervision, linehaul operations

**Proposed action:** Add recognized variants to the rule: Transportation supervision, dispatch supervision, fleet supervision, linehaul operations.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.

<sub>Sources: rule:Q2, knowledge:skill.transportation-supervision. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.transportation-supervision.</sub>

Decision: **Pending human decision**

### Q2 counts experience only under specific job titles

`SA-REQ-LH-0217-b7263005` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `experience_path_narrower`

Rule Q2 only counts experience held under the titles 'Transportation Supervisor', 'Dispatch Supervisor'. The underlying capability can be demonstrated under other titles and in other domains.

**Evidence**
- `rule:Q2` — 3 years as Transportation Supervisor or Dispatch Supervisor (by job title).

**Consequence in the supplied candidate sample:** 2 candidate(s) would pass this rule under this correction alone (C-302, C-303); 1 candidate-review opportunity depends on it (C-303).

**Proposed action:** Count relevant experience by responsibilities, not titles: match recognized terminology across the full résumé and route equivalency evidence to recruiter review.

**Expected benefit:** Candidates whose titles differ from the conventional path reach human review.  
**Trade-off:** Responsibility-based matching needs recruiter verification; expect modest extra review time.

**Limitations**
- Whether alternative experience is equivalent must be judged by a recruiter or hiring manager.
- Title-based counting may reflect a deliberate employer choice; confirm intent.

<sub>Sources: rule:Q2, requirement:R2. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.transportation-supervision.fleet-coordination.</sub>

Decision: **Pending human decision**

## 5. Candidate-review opportunities

### Candidate C-303 may meet the requirements through a path the current rules do not recognize

`SA-REQ-LH-0217-6f063ac1` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `candidate_review_opportunity`

C-303 was rejected by Q1, Q2. Under the proposed corrections they pass every rule, and each required requirement has supporting evidence.

**What requirements might this person satisfy, and what evidence supports it?**

| Req | Stated | Status | Path | Evidence |
|---|---|---|---|---|
| R1 | required | Evidenced | different terminology | `credentials.s1` Class A CDL |
| R2 | required | Evidenced via alternative path (48 mo) | transferable experience (eq.transportation-supervision.fleet-coordination) | `experience[0].s1` Supervised 14 linehaul drivers and scheduled daily routes.<br>`experience[0].s2` Ran hours-of-service compliance audits. |
| R3 | required | Evidenced | same terminology | `experience[0].s2` Ran hours-of-service compliance audits. |

**Excluded by:** Q1 — listed credential not held; Q2 — 0 relevant months vs 36 required

**How their path differs from the conventional one**
- R1 described in different terminology: Class A CDL
- R2 evidenced through transferable experience (eq.transportation-supervision.fleet-coordination)
- Experience domains: logistics

**What remains unproven**
- R2: eq.transportation-supervision.fleet-coordination: 3 of 3 indicators present; 48 months of relevant experience. Conditions: Must include direct supervision or scheduling of drivers.
- Qualification has not been established by this analysis.

**What the recruiter should verify next**
- Confirm number of drivers supervised and authority over scheduling.
- Confirm compliance responsibilities.

<sub>Sources: candidate:C-303, rule:Q1, rule:Q2. Knowledge: `core@1.1.0+8a94e741e4`; records: eq.transportation-supervision.fleet-coordination.</sub>

Decision: **Pending human decision**

## 6. Recommended changes

Suggested configuration changes, for the employer to implement in the ATS. Nothing is applied automatically.

**Q1** — Must hold CDL Class A.  
Proposed by: `SA-REQ-LH-0217-24c327f3` (pending)

```yaml
suggested_logic:
  credentials:
  - CDL Class A
  - Commercial driver's license (Class A)
  - Class A CDL
  - CDL-A
  - Class A commercial driver's license
  - commercial driver license class A
```

**Q2** — 3 years as Transportation Supervisor or Dispatch Supervisor (by job title).  
Proposed by: `SA-REQ-LH-0217-bdfae568` (pending), `SA-REQ-LH-0217-b7263005` (pending)

```yaml
suggested_logic:
  terms:
  - Transportation Supervisor
  - Dispatch Supervisor
  - Transportation supervision
  - dispatch supervision
  - fleet supervision
  - linehaul operations
  years: 3
  field: resume
  equivalencies:
  - eq.transportation-supervision.fleet-coordination
```

## 7. Human decisions and rationale

_No decisions recorded yet. Record them in `decisions.yaml` (or export from the HTML report) and re-run._

## 8. Outcome measurements

_No outcome data supplied yet. Add `outcomes.yaml` with a documented baseline after corrections are implemented._

## Appendix A — Candidates assessed but not surfaced

| Candidate | ATS status | Excluded by | Reason |
|---|---|---|---|
| C-301 | advanced | — | Not excluded by the ATS (status: advanced). |
| C-302 | rejected | Q1, Q2 | Does not meet a protected requirement; not surfaced. |
| C-304 | rejected | Q2 | Still excluded after proposed corrections by Q2. |

## Appendix B — Protected and suppressed items

- candidate `C-302`: Does not meet a protected requirement; not surfaced.
- rule `Q1`: Commercial driver's license (Class A) is a regulated credential in the knowledge base
