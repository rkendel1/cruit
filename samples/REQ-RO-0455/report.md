# Requisition assurance report — Revenue Operations Manager (REQ-RO-0455)

Job family `revenue-operations` · employer `northwind` · knowledge `core@1.1.0+8a94e741e4` (approved) · engine 0.2.0 · run 2026-11-03T12:00:00Z

> This report recommends changes and human review. It does not reject, advance or hire anyone, and it does not claim any candidate was wrongly excluded. Level 1 findings are established by the supplied materials; Level 2 findings are risks that need human judgement; Level 3 findings are measured outcomes.

## Summary

- **2** demonstrable inconsistencies (Level 1)
- **3** missed-talent risks and review opportunities (Level 2), including **0** candidate(s) of 0 assessed surfaced for human review
- **0** measured outcomes (Level 3)
- **5** findings awaiting a human decision

**Inputs received:** job description: `supplied`, screening configuration: `recruiter_documentation`, candidate evidence: `not_supplied`

**Limitations of this run**
- Screening rules were supplied as recruiter documentation, not verified ATS configuration. Findings describe the documented rules; the live ATS may differ.
- No authorized candidate evidence was supplied; candidate-pool assurance was not performed.
- Candidate evidence is matched deterministically against the knowledge pack; language-model interpretation is not used in this run.

## 1. Requirements and stated intent

| ID | Requirement | Stated as | Proposed classification | Basis |
|---|---|---|---|---|
| R1 | 5+ years of revenue operations experience. | required | Essential | linked to objectives ['O1'] |
| R2 | Salesforce administration experience. | required | Essential | Northwind's go-to-market stack runs on Salesforce and this role is its administrator. |
| R3 | MBA or equivalent business education. | preferred | Preferred | stated as preferred in the posting |

🔒 = protected (legal, licensing or employer non-negotiable). No alternative path is ever proposed for protected requirements.

## 2. Screening rules inspected

| Rule | Type | Action | Linked requirement | Status | Findings |
|---|---|---|---|---|---|
| Q1 | minimum_experience | reject | R1 | correction proposed | 3 |
| Q2 | knockout_question | reject | R3 | correction proposed | 1 |
| Q3 | keyword_filter | reject | R1 | correction proposed | 1 |

## 3. Confirmed inconsistencies and protected requirements

### Q1 requires 7 years; the posting asks for 5

`SA-REQ-RO-0455-4d7c87e1` · Level 1 · Demonstrable inconsistency · confidence **high** · check `threshold_inconsistency`

Requirement R1 states 5+ years, but rule Q1 enforces 7 years.

**Evidence**
- `requirement:R1` — 5+ years of revenue operations experience.
- `rule:Q1` — years: 7 — 7 years as Revenue Operations Manager (by job title).

**Proposed action:** Align the rule threshold with the posted requirement (5 years), or update the posting if the higher threshold is genuinely required.

**Expected benefit:** Applicants who meet the posted threshold are no longer silently excluded.  
**Trade-off:** None if the posting reflects the real need.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation:** not evaluated — No candidate evidence was supplied, so candidate impact cannot be verified. This remains a rule-level risk.

<sub>Sources: requirement:R1, rule:Q1. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

### Preferred qualification R3 is enforced as a knockout by Q2

`SA-REQ-RO-0455-30380d96` · Level 1 · Demonstrable inconsistency · confidence **high** · check `preferred_enforced_as_knockout`

Requirement R3 is stated as preferred, but rule Q2 rejects applicants who do not meet it.

**Evidence**
- `requirement:R3` — stated_as: preferred — MBA or equivalent business education.
- `rule:Q2` — action: reject — Do you hold an MBA?

**Proposed action:** Convert the rule into a scoring or ranking signal, or reclassify the requirement as essential with a documented rationale.

**Expected benefit:** Applicants who meet all essential requirements are no longer rejected for lacking a preference.  
**Trade-off:** More applicants reach review; ranking should still favour the preferred qualification.

**Screening-risk category:** Preferred criterion enforced as a knockout

**Correction simulation:** not evaluated — No candidate evidence was supplied, so candidate impact cannot be verified. This remains a rule-level risk.

<sub>Sources: requirement:R3, rule:Q2. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

## 4. Potential missed-talent risks

### Q1 matches literally and misses recognized variants of Revenue operations

`SA-REQ-RO-0455-088d343c` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q1 matches only 'Revenue Operations Manager'. The knowledge base records 3 equivalent term(s) for Revenue operations that the rule does not recognize.

**Evidence**
- `knowledge:skill.revenue-operations` — recognized variant(s): Revenue operations, RevOps, revenue ops

**Proposed action:** Add recognized variants to the rule: Revenue operations, RevOps, revenue ops.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- Terminology only; scope of revenue operations roles varies by organization.
- Closely related (not equivalent) terms not proposed: commercial operations, sales operations, sales ops. Verify case by case.

**Screening-risk category:** Terminology not recognized

**Correction simulation:** not evaluated — No candidate evidence was supplied, so candidate impact cannot be verified. This remains a rule-level risk.

<sub>Sources: rule:Q1, knowledge:skill.revenue-operations, knowledge:term.revenue-operations. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.revenue-operations, term.revenue-operations.</sub>

Decision: **Pending human decision**

### Q1 counts experience only under specific job titles

`SA-REQ-RO-0455-568981f2` · Level 2 · Plausible missed-talent risk · confidence **medium** · check `experience_path_narrower`

Rule Q1 only counts experience held under the titles 'Revenue Operations Manager'. The underlying capability can be demonstrated under other titles and in other domains.

**Evidence**
- `rule:Q1` — 7 years as Revenue Operations Manager (by job title).

**Proposed action:** Count relevant experience by responsibilities, not titles: match recognized terminology across the full résumé and route equivalency evidence to recruiter review.

**Expected benefit:** Candidates whose titles differ from the conventional path reach human review.  
**Trade-off:** Responsibility-based matching needs recruiter verification; expect modest extra review time.

**Limitations**
- Whether alternative experience is equivalent must be judged by a recruiter or hiring manager.
- Title-based counting may reflect a deliberate employer choice; confirm intent.

**Screening-risk category:** Rule narrower than the requirement

**Correction simulation:** not evaluated — No candidate evidence was supplied, so candidate impact cannot be verified. This remains a rule-level risk.

<sub>Sources: rule:Q1, requirement:R1. Knowledge: `core@1.1.0+8a94e741e4`.</sub>

Decision: **Pending human decision**

### Q3 matches literally and misses recognized variants of Revenue operations

`SA-REQ-RO-0455-130b17ea` · Level 2 · Plausible missed-talent risk · confidence **high** · check `literal_term_missing_variants`

Rule Q3 matches only 'RevOps'. The knowledge base records 3 equivalent term(s) for Revenue operations that the rule does not recognize.

**Evidence**
- `knowledge:skill.revenue-operations` — recognized variant(s): Revenue operations, revenue operations manager, revenue ops

**Proposed action:** Add recognized variants to the rule: Revenue operations, revenue operations manager, revenue ops.

**Expected benefit:** Applicants describing the same work in different words are no longer filtered out.  
**Trade-off:** Ambiguous abbreviations can admit unrelated profiles; review ambiguity notes first.

**Limitations**
- Synonyms improve recognition; they do not establish competence.
- Terminology only; scope of revenue operations roles varies by organization.
- Closely related (not equivalent) terms not proposed: commercial operations, sales operations, sales ops. Verify case by case.

**Screening-risk category:** Terminology not recognized

**Correction simulation:** not evaluated — No candidate evidence was supplied, so candidate impact cannot be verified. This remains a rule-level risk.

<sub>Sources: rule:Q3, knowledge:skill.revenue-operations, knowledge:term.revenue-operations. Knowledge: `core@1.1.0+8a94e741e4`; records: skill.revenue-operations, term.revenue-operations.</sub>

Decision: **Pending human decision**

## 5. Candidate-review opportunities

_None found._

## 6. Recommended changes

Suggested configuration changes, for the employer to implement in the ATS. Nothing is applied automatically.

**Q1** — 7 years as Revenue Operations Manager (by job title).  
Proposed by: `SA-REQ-RO-0455-4d7c87e1` (pending), `SA-REQ-RO-0455-088d343c` (pending), `SA-REQ-RO-0455-568981f2` (pending)

```yaml
suggested_logic:
  terms:
  - Revenue Operations Manager
  - Revenue operations
  - RevOps
  - revenue ops
  years: 5
  field: resume
  equivalencies: []
```

**Q2** — Do you hold an MBA?  
Proposed by: `SA-REQ-RO-0455-30380d96` (pending)

```yaml
suggested_logic:
  removed: true
```

**Q3** — Résumé must mention RevOps.  
Proposed by: `SA-REQ-RO-0455-130b17ea` (pending)

```yaml
suggested_logic:
  terms:
  - RevOps
  - Revenue operations
  - revenue operations manager
  - revenue ops
  match: any
  field: resume
```

## 7. Human decisions and rationale

_No decisions recorded yet. Record them in `decisions.yaml` (or export from the HTML report) and re-run._

## 8. Outcome measurements

_No outcome data supplied yet. Add `outcomes.yaml` with a documented baseline after corrections are implemented._

## Appendix A — Candidates assessed but not surfaced

_None._
