# Screening Assurance — product design and implementation blueprint (v1.0)

_Source document for this repository's MVP. Reproduced as supplied._

The product should be designed around a stronger thesis than “catch candidates an ATS misses.”

It helps employers get more value from the recruiting systems and processes they already pay for, while deliberately expanding their ability to recognize nontraditional talent and transferable skills.

An ATS is designed to manage applicants and hiring workflows. Screening Assurance complements it by improving how job requirements are expressed, how qualifications are interpreted, and how screening decisions are evaluated. It does not replace the ATS, create another applicant database, or take hiring authority away from recruiters.

The differentiator is intentionality: conventional screening tends to reward candidates who resemble the expected profile. This product helps employers recognize candidates who can deliver the required outcomes through different combinations of skills, experiences, and career paths.

That calls for a complete design: product strategy, knowledge architecture, diagnostic engine, recruiter workflow, evaluation methodology, governance, integration, and commercial model.

Screening Assurance

A talent-intelligence and screening-quality layer for existing ATS platforms

Product design and implementation blueprint — v1.0

1. Product vision

Help employers get more value from the recruiting systems, processes, and investments they already have by making their screening practices more effective, more defensible, and more capable of recognizing talent beyond traditional career paths.

Organizations spend heavily to attract applicants, purchase recruiting technology, build employer brands, engage recruiters, and compete for talent. Yet the process used to narrow applicant pools can unintentionally eliminate people whose experience does not resemble the conventional profile for a role.

A candidate may possess the required capabilities through a different industry, a combination of complementary skills, adjacent professional experience, self-directed learning, or responsibilities that never carried the expected job title.

Screening Assurance helps employers identify those possibilities before valuable talent is lost.

It works alongside existing applicant tracking systems (ATS). It does not replace them, become another system of record, or make hiring decisions. It improves the quality of the requirements, rules, interpretations, and review processes employers already use.

Product promise

Help organizations:

* Protect the value of their recruiting technology and talent acquisition investments.
* Find credible candidates who might otherwise be overlooked by rigid or overly literal screening.
* Recognize transferable skills and combinations of skills that traditional job histories fail to communicate.
* Reduce preventable exclusion without lowering legitimate job requirements.
* Give recruiters evidence-backed recommendations they can act on within their existing workflows.
* Learn continuously which screening practices improve the quality and breadth of the candidate pool.

Core principle

Do not lower the bar. Improve the organization’s ability to recognize who can clear it.

⸻

2. The problem

Traditional screening must convert a complex human capability profile into operational rules. This is necessary at scale, but it creates several failure modes.

2.1 Terminology mismatch

A job description uses one term, while a candidate describes substantially similar work using another.

Examples include:

* Customer success versus client success.
* Site reliability engineering versus production reliability.
* Revenue operations versus commercial operations.
* Program leadership versus cross-functional delivery.

The terms may be equivalent in some contexts, but not universally. The system must recognize context rather than simply expanding a list of keywords.

2.2 Experience-path rigidity

The employer requires experience in a particular role, industry, or technology even when that experience is only one possible way to demonstrate the underlying capability.

For example, a role requiring incident management may overlook a candidate who has led crisis response in healthcare, infrastructure, or logistics because their résumé does not contain the expected title or terminology.

The relevant question is whether the candidate can demonstrate the required capability—not whether their career followed the conventional path.

2.3 Fragmented skill recognition

Candidates often possess multiple complementary skills. Their combined value may be greater than any single credential or job title suggests.

A candidate might combine:

* Technical expertise.
* Operational execution.
* Customer communication.
* Data analysis.
* Cross-functional leadership.

Conventional screening can treat these as disconnected attributes rather than evidence of a valuable capability profile.

Screening Assurance should help employers discover these combinations while requiring evidence that they matter for the specific role.

2.4 Excessive or contradictory requirements

A job description may label numerous qualifications as mandatory even though the actual job requires only a smaller subset. Different screening questions may also enforce inconsistent interpretations of the same requirement.

The product identifies these inconsistencies and asks the employer to resolve them before they unnecessarily constrain the candidate pool.

2.5 Lost recruiting investment

Every preventable exclusion can waste some portion of the employer’s investment in advertising, sourcing, recruiter time, application processing, and hiring technology.

The cost is not just a missed hire. It is also the possibility of repeating sourcing efforts because the original process failed to recognize suitable candidates already in the pipeline.

The product must make this economic problem measurable without pretending every excluded applicant was qualified.

⸻

3. Product boundaries

Screening Assurance is a complementary quality and talent-intelligence layer.

Existing ATS responsibility	Screening Assurance responsibility
Manage requisitions and applicants	Examine the quality of screening criteria
Store candidate records	Analyze authorized candidate evidence
Execute configured workflows	Identify potentially restrictive rules and inconsistencies
Manage recruiter collaboration	Supply evidence-backed review recommendations
Track hiring stages	Measure outcomes associated with approved screening changes
Support hiring decisions	Help humans recognize credible, nontraditional qualification paths

Explicit non-goals

The product will not:

* Replace an ATS or require recruiters to migrate their applicant database.
* Become an independent candidate sourcing marketplace in v1.
* Automatically reject, advance, or hire applicants.
* Treat semantic similarity as proof of qualification.
* Assume that all transferable skills are equivalent.
* Recommend lowering genuine legal, safety, licensing, or job-critical requirements.
* Claim a candidate was wrongly rejected solely because a diagnostic model believes they could be qualified.
* Claim access to actual ATS configuration unless that configuration was supplied or retrieved through an authorized integration.

The product recommends better screening practices and additional review. The employer retains decision-making authority.

⸻

4. Product experience

The product has four connected capabilities.

A. Screening Design Assurance

Before a job is published, inspect the requirements and operational screening rules for unnecessary restrictions, contradictions, and missed ways to demonstrate competence.

B. Candidate Pool Assurance

After applications begin arriving, analyze authorized candidate evidence to identify potentially qualified people who may have been filtered out or deprioritized by restrictive criteria.

This is particularly important when the ATS has already removed applicants from the active recruiter workflow.

C. Transferable Skills Intelligence

Maintain a versioned knowledge base of terminology, skills, equivalencies, and cross-domain relationships that helps the system recognize nontraditional career paths.

D. Outcome and Investment Assurance

Measure whether approved changes increase meaningful candidate review, improve qualified-candidate yield, and reduce avoidable recruiting work.

These are parts of one product lifecycle, not four disconnected products.

⸻

5. End-to-end workflow

The product follows a continuous assurance loop.

Connect → Define → Diagnose → Review → Correct → Observe → Learn

Step 1: Connect

A recruiter or recruiting operations leader selects a requisition from an authorized ATS integration or provides an export.

Inputs may include:

* Job description and requisition metadata.
* Required and preferred qualifications.
* Screening questions and knockout rules.
* Configured scoring or matching criteria, when available.
* Candidate evidence and relevant application-stage data, when authorized.

The system records which inputs it actually received. It must distinguish a supplied job description from verified ATS configuration.

Step 2: Define the role’s real requirements

The product helps the employer distinguish:

* Essential: Required to perform the job or meet a legitimate constraint.
* Preferred: Valuable, but not necessary for consideration.
* Demonstrable through alternatives: Can be established through multiple types of evidence.
* Unverified assumption: A requirement whose necessity needs human clarification.

For each essential requirement, the system asks what successful performance looks like and what evidence could reasonably demonstrate it.

A required professional license, for example, is not interchangeable with adjacent experience. By contrast, a requirement for a particular tool may allow equivalent experience if the employer agrees the underlying capability is transferable.

Step 3: Diagnose the screening design

The diagnostic engine compares stated job intent with operational screening rules and candidate evidence, where available.

It looks for:

* Literal terminology that excludes recognized variants.
* Experience requirements that may be narrower than the actual capability needed.
* Required qualifications that appear inconsistent with the job’s stated objectives.
* Screening questions that contradict the job description.
* Skill relationships or transferable evidence that the process cannot recognize.
* Candidate profiles that may satisfy requirements through nontraditional paths.
* Requirements whose business necessity is unclear.

Every finding identifies the source rule, supporting evidence, confidence, limitations, and recommended action.

Step 4: Human review

The recruiter or hiring manager reviews each finding.

They may:

* Confirm the requirement is necessary.
* Accept a proposed terminology or equivalency change.
* Request additional evidence.
* Reclassify a requirement from mandatory to preferred.
* Approve a targeted review of overlooked candidates.
* Reject the recommendation and record the reason.

The system must never silently change the employer’s screening rules.

Step 5: Correct the process

The employer implements approved changes in the ATS or recruiting workflow.

Depending on integration capabilities, Screening Assurance may generate a suggested configuration change, create a review list, or provide instructions for a manual update. Changes are not applied automatically without explicit authorization.

Step 6: Observe results

The product measures what changed:

* How many candidates became eligible for review?
* How many were genuinely relevant after human assessment?
* Did qualified-candidate yield improve?
* Did recruiter workload increase or decrease?
* Did downstream stage progression change?
* Were any new risks introduced?

Step 7: Learn

The product uses verified outcomes to improve future diagnostics and knowledge revisions.

A recruiter-confirmed equivalency may inform a future recommendation, but it does not automatically become a universal rule. Learning must preserve context, provenance, and approval.

⸻

6. The knowledge architecture

This is a core differentiator.

The matching and diagnostic engine should remain relatively stable while the knowledge that informs it can be edited, tested, versioned, and improved without changing application code.

The initial knowledge system consists of three independently maintainable document families.

6.1 Synonyms and terminology

Purpose: Recognize alternate terminology that may express the same concept.

A record should include:

* Canonical term.
* Alternative terms and abbreviations.
* Applicable job families or contexts.
* Relationship type.
* Confidence and supporting sources.
* Known ambiguities and exclusions.
* Version, author, and rationale.

Example:

Canonical term: Site reliability engineering.

Variants: SRE, production reliability engineering, reliability engineering.

Context: Software infrastructure and operations.

Constraint: The presence of a related term does not prove that the candidate possesses the required experience.

Synonyms improve recognition; they do not establish competence.

6.2 Equivalencies and transferable experience

Purpose: Define when different experiences or forms of evidence may demonstrate the same underlying capability.

A record should include:

* Target requirement or capability.
* Alternative evidence that may satisfy it.
* Conditions under which the equivalency applies.
* Evidence needed to validate the claim.
* Limitations and non-equivalencies.
* Applicable roles and contexts.
* Confidence, provenance, and review status.

Example:

Target capability: Incident management.

Potential alternative evidence: Leading operational crisis response, coordinating recovery across teams, managing incident communications, and conducting post-incident reviews.

Conditions: Evidence must demonstrate relevant responsibilities and complexity, not merely participation in an event.

This distinction is central to the product. Similar experience is not automatically equivalent experience.

6.3 Skills and capability relationships

Purpose: Represent skills as structured, contextual capabilities rather than a flat keyword list.

A skill record should include:

* Canonical skill identifier and definition.
* Alternate names.
* Related and prerequisite skills.
* Proficiency expectations.
* Evidence types that can demonstrate the skill.
* Relevant contexts and job families.
* Explicitly non-equivalent relationships.
* Sources, confidence, and version.

The system should support relationships such as:

* Equivalent terminology.
* Closely related skill.
* Prerequisite for another skill.
* Evidence supporting a capability.
* Potentially transferable across domains.
* Not equivalent without additional evidence.

It should also recognize skill combinations. For example, technical analysis plus stakeholder communication plus operational leadership may provide evidence of cross-functional problem-solving. The combination should be surfaced only when relevant to the role’s actual needs.

6.4 Knowledge must be data, not code

These documents should be stored in a structured, machine-readable format with a human-editable representation.

The system must allow authorized users to:

1. Edit a record.
2. Validate its schema and relationships.
3. Create a versioned revision.
4. Run regression tests.
5. Compare diagnostic results with the previous version.
6. Review and approve the revision.
7. Promote it to the intended environment.
8. Roll back if results deteriorate.

The documents can begin as version-controlled YAML or JSON. The product does not need a new database or a complex knowledge-management service to prove the concept.

A graphical editor can follow once the underlying contracts and workflow have been validated.

6.5 General knowledge versus employer policy

These must remain separate.

General knowledge describes terminology, skill relationships, and potential transferable evidence.

Employer policy describes what a particular organization requires for a particular job, including legitimate non-negotiable qualifications.

Requisition configuration describes the actual screening rules being applied to the current job.

The diagnostic engine evaluates all three. General knowledge must never silently override employer requirements.

⸻

7. The diagnostic engine

The engine has five logical stages.

Stage 1: Normalize

Extract and normalize requirements, terminology, skills, screening questions, and candidate evidence.

Preserve the original source text and identifiers so every conclusion can be traced back to its origin.

Stage 2: Interpret

Use the versioned knowledge documents to identify relevant concepts, alternate terminology, skill relationships, and possible transferable evidence.

Language models may assist with extraction and interpretation, but their output remains a hypothesis until checked against the evidence and applicable rules.

Stage 3: Evaluate

Run deterministic checks wherever possible:

* Is a requirement mandatory in one place and optional in another?
* Does a screening question enforce an unstated requirement?
* Is a recognized terminology variant absent from a literal matching rule?
* Is an alternative qualification permitted by employer policy?
* Could a candidate have been excluded by a particular rule?

For less deterministic questions, produce a review finding rather than an automatic conclusion.

Stage 4: Explain

Each finding contains:

* Finding identifier.
* Requisition and source-rule reference.
* Relevant knowledge version.
* Observed inconsistency or exclusion risk.
* Supporting evidence.
* Confidence and limitations.
* Proposed corrective action.
* Expected operational benefit.
* Potential downside or trade-off.
* Human disposition.

Stage 5: Measure

After an approved change, compare the resulting candidate-review and hiring-process outcomes with a documented baseline.

The product must distinguish a detected risk from a confirmed inconsistency and from a measured improvement.

⸻

8. Evidence and confidence model

Every diagnostic finding belongs to one of three evidence levels.

Level 1: Demonstrable inconsistency

The available materials directly establish a discrepancy.

Example: The job description explicitly accepts equivalent experience, but a configured screening question rejects candidates who lack one named credential regardless of equivalent evidence.

Level 2: Plausible missed-talent risk

The available evidence suggests a candidate or candidate group may be overlooked, but qualification has not been established.

Example: A candidate has substantial relevant operational experience under a different job title, but a hiring manager needs to assess whether that experience meets the role’s expectations.

Level 3: Measured impact

The employer has reviewed the affected candidates or changed the screening process, and observed outcomes are available.

Example: A revised screening rule leads to additional recruiter-reviewed candidates, several of whom are confirmed to meet the role’s requirements.

The system must not collapse these categories into a single score or label all flagged candidates as false negatives.

⸻

9. Recruiter experience and interface

The primary user experience should focus on decisions, not AI-generated prose.

9.1 Portfolio overview

A recruiting operations dashboard shows:

* Requisitions reviewed.
* Findings awaiting decisions.
* Confirmed screening inconsistencies.
* Approved corrections.
* Candidate-review opportunities.
* Outcome measurements.
* Repeated patterns across job families.

The dashboard should prioritize actionable work rather than the raw number of warnings.

9.2 Requisition assurance report

Each requisition has a clear report organized into:

1. Requirements and stated intent.
2. Screening rules inspected.
3. Confirmed inconsistencies.
4. Potential missed-talent risks.
5. Candidate-review opportunities.
6. Recommended changes.
7. Human decisions and rationale.
8. Outcome measurements.

Recruiters can accept, reject, or defer individual recommendations.

9.3 Candidate evidence review

Where authorized candidate data is available, present the specific requirement and the evidence that may satisfy it.

The interface should answer:

* What requirement might this person satisfy?
* What evidence supports that possibility?
* How does their experience differ from the conventional path?
* What remains unproven?
* What should a recruiter verify next?

It should not lead with a generic AI match percentage. A percentage can conceal unsupported assumptions and imply precision the system does not possess.

9.4 Knowledge management

An authorized administrator can inspect and edit the synonym, equivalency, and skill documents; review provenance; compare revisions; run tests; and approve changes.

Recruiters should be able to submit proposed knowledge corrections without being granted permission to alter shared production rules.

⸻

10. ATS integration strategy

The product succeeds by fitting into existing recruiting operations.

Initial integration

Start with a controlled workflow using requisition exports, screening-rule documentation, and authorized candidate data.

The first version should demonstrate useful findings before investing heavily in deep integrations.

Subsequent integration

Add ATS-specific connectors that can retrieve relevant data through authorized APIs and, where supported, submit review lists or proposed configuration changes.

The integration contract should define:

* Read permissions.
* Permitted candidate data.
* Requisition and candidate identifiers.
* Screening-rule access.
* Write permissions, if any.
* Approval requirements.
* Audit events.
* Retention and deletion behavior.

The ATS remains the system of record. Screening Assurance stores only the information required to perform its function, subject to the employer’s retention and security requirements.

If the ATS does not expose its actual screening configuration, the product must disclose that limitation rather than claiming a complete audit.

⸻

11. Protecting recruiting investment

The commercial value should be expressed in operational terms, not inflated claims about the value of every overlooked candidate.

Potential sources of value

* Better utilization of existing ATS capabilities.
* Fewer unnecessary sourcing cycles.
* Less time spent manually reconciling inconsistent requirements.
* More relevant candidates reaching human review.
* Improved visibility into the consequences of screening rules.
* Reduced avoidable rework when a candidate pool is too narrow.
* Better recognition of nontraditional talent already present in the applicant pool.

Value measurement

Establish a baseline for each pilot:

* Recruiting spend or relevant cost proxy.
* Number of applicants and recruiter-reviewed candidates.
* Qualified-candidate yield.
* Recruiter time per qualified candidate.
* Time to reach a sufficiently qualified shortlist.
* Additional review volume caused by changes.
* Downstream stage progression and eventual hiring outcomes where available.

Report measured savings separately from estimated savings. Do not attribute every improvement to the product without a credible comparison.

A practical economic metric is:

Incremental qualified candidates identified per unit of recruiter effort.

This tests whether the product helps employers recognize more relevant talent without overwhelming recruiters with low-quality leads.

⸻

12. Trust, fairness, and governance

Employment screening is consequential. A useful product must be auditable, conservative in its claims, and designed to prevent new forms of exclusion.

Required safeguards

* Human authority over hiring and screening decisions.
* Traceable evidence for each recommendation.
* Versioned knowledge and diagnostic rules.
* Explicit confidence and uncertainty.
* Protection of sensitive candidate data.
* Access controls and audit logs.
* Review of potential disparate impact where appropriate and lawful.
* Documented reasons for approving or rejecting significant changes.
* Reproducible results using the same inputs and knowledge versions.
* Tests for both missed opportunities and false positives.

The product should not infer protected characteristics or use them to determine whether a candidate should advance. Fairness evaluation must follow applicable law, organizational policy, and appropriate privacy controls.

It should also avoid the opposite failure: removing legitimate requirements in the name of inclusion. The objective is broader recognition of valid evidence, not indiscriminate relaxation of standards.

⸻

13. Validation and launch plan

Phase 1: Validate the problem

Interview 10–15 recruiting operations leaders and experienced recruiters.

Learn:

* How screening rules are established.
* Which ATS controls are actually used.
* Where nontraditional candidates are lost.
* How recruiters handle exceptions today.
* What evidence would persuade them to change a rule.
* Who owns the budget for screening quality.
* What security and integration requirements would block adoption.

Seek a design partner willing to provide a de-identified requisition, relevant screening rules, and a permitted sample of candidate evidence.

Phase 2: Run a managed-service pilot

Begin with one job family and a limited set of requisitions.

Provide:

* A requirement and screening-rule audit.
* A versioned terminology and transferable-skills analysis.
* Evidence-backed findings.
* Proposed corrections.
* A human-review process.
* A post-change outcome report.

Manually validate findings with an experienced recruiter or hiring manager. The first objective is to establish that the diagnostics are useful, not to automate every step.

Phase 3: Build the repeatable product

Once the workflow is validated, build:

* Structured knowledge-document contracts.
* A deterministic diagnostic engine.
* A versioned evaluation harness.
* A review and approval interface.
* Requisition-level reporting.
* Basic ATS data import.
* Outcome tracking.

Phase 4: Integrate and scale

Introduce deeper ATS integrations, organizational policy controls, knowledge-management tooling, and portfolio-level reporting after customers demonstrate recurring demand.

⸻

14. Initial success criteria

The pilot should establish explicit acceptance criteria before testing.

Suggested measures:

* Proportion of findings independently confirmed by recruiting experts.
* Proportion of findings that lead to an actionable decision.
* Rate of accepted versus rejected recommendations, with reasons.
* Number of additional candidates receiving meaningful human review.
* Proportion of additionally reviewed candidates confirmed to meet requirements.
* Change in recruiter effort per qualified candidate.
* Time required to complete the assurance review.
* Recurrence of the same screening defects across requisitions.
* Customer willingness to pay and reuse the process.

The product must track false positives and review burden alongside additional candidates surfaced. More candidates is not automatically better.

⸻

15. Business model

Start as a managed screening-assurance service, with a path toward recurring software revenue.

Pilot

A fixed-fee engagement covering a defined number of requisitions, a single job family, and a documented outcome report.

Recurring service

A per-requisition package or monthly allowance for organizations with regular hiring activity.

Enterprise product

An annual subscription based on recruiting volume, organizational complexity, integration requirements, and governance needs.

Pricing should reflect the value of the assurance workflow and the volume of work supported—not the number of candidates flagged or the number of alleged false negatives.

The likely initial buyer is a recruiting operations or talent acquisition operations leader who has both recurring requisition volume and an incentive to improve recruiting efficiency.

⸻

16. What makes the product defensible

The long-term value is not a proprietary synonym list or a generic language model.

It is the combination of:

* A structured, editable knowledge base for skills and transferable experience.
* A reproducible diagnostic engine.
* A growing library of validated screening defects and corrective patterns.
* Traceable evidence connecting recommendations to actual requirements.
* Workflow integration with existing recruiting systems.
* Outcome data showing which corrections are useful.
* Organizational trust built through governance and auditability.

Over time, the product can become an assurance layer that helps organizations systematically improve their screening practices across job families and requisitions.

Its advantage comes from learning which changes produce better decisions—not simply generating more semantic matches.

⸻

17. Product principles

1. Complement, never replace, the ATS.
2. Protect recruiting investment by improving the existing process.
3. Recognize capability, not just career-path conformity.
4. Treat transferable skills as evidence to evaluate, not automatic equivalencies.
5. Keep synonyms, equivalencies, and skills externally editable and versioned.
6. Separate general knowledge from employer policy and live requisition configuration.
7. Make every recommendation explainable and traceable.
8. Preserve human authority over consequential decisions.
9. Measure qualified-candidate yield and recruiter effort, not raw match volume.
10. Use real outcomes to improve knowledge, while preserving provenance and approval.
11. Build the smallest useful system before investing in extensive integrations.
12. Never claim an exclusion was wrongful unless the evidence supports that conclusion.

18. Final product thesis

Organizations have already invested in systems to attract, organize, and evaluate talent. Screening Assurance helps them use those investments more effectively.

It makes screening criteria more consistent with actual job needs, expands recognition of credible transferable skills, and gives recruiters a practical way to examine candidates who may have been overlooked because their experience does not fit the conventional template.

The product does not promise that every unconventional candidate is qualified. It promises a better process for finding out.

The vision: a recruiting process that maintains high standards while deliberately recognizing talent through more than one career path—and that can demonstrate whether its screening practices are helping or hindering that goal.

My recommendation on what to build first

The full vision is broader than the first implementation. I would keep the initial build focused on proving one thing: Can we identify and validate preventable screening exclusions using knowledge that can change without code changes?

The first engineering milestone should contain:

* Knowledge contracts for synonyms, equivalencies, and skills, including provenance, context, non-equivalencies, and versions.
* A diagnostic engine that accepts a requisition and screening rules, and produces traceable findings.
* An evaluation harness with realistic conventional and nontraditional candidate examples, plus before/after comparison when knowledge changes.
* A human review report that distinguishes confirmed inconsistencies from potential missed-talent opportunities.
* A pilot measurement plan that establishes whether additional candidates are genuinely qualified and whether recruiter effort is justified.

Do not start with ATS integrations, an elaborate dashboard, or a large general-purpose skills ontology. First prove the diagnostic loop against real recruiting workflows.

The strategic positioning is important, too: this is not an inclusion add-on and not an ATS competitor. It is screening quality assurance that protects recruiting ROI while helping employers recognize qualified talent they might otherwise miss.