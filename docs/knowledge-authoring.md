# Knowledge authoring

The knowledge pack lets the diagnostic engine recognize nontraditional qualification paths **without code
changes**. Because it influences who reaches human review, it is edited like production configuration:
versioned, validated, evaluated, approved, and reversible.

## Roles

| Role | Can do |
|---|---|
| Recruiter / hiring manager | Submit proposals (`sa knowledge propose`, or flag a decision with `propose_knowledge_update: true`). Cannot change shared knowledge. |
| Knowledge administrator | Edit `knowledge/pack/`, run validation and evals, set `status: approved`, release, promote, roll back. |

## Workflow

1. **Edit a record** in `knowledge/pack/*.yaml`. Increment the record's `version` and update
   `provenance.updated`. (`sa knowledge diff` warns when a changed record keeps its version.)
2. **Validate**: `sa knowledge validate`. Checks schema, unique ids, dangling references, contradictory
   relationships, equivalencies targeting regulated credentials, and the same term mapping to different
   concepts in overlapping contexts without a documented ambiguity.
3. **Create a revision**: bump `version` in `manifest.yaml`, add a `changelog` entry, set `status: in_review`.
4. **Run regression tests**: `sa eval`. Add or update a labeled case in `evals/cases/` that exercises the change,
   including a *forbidden* finding for the false positive you are worried about.
5. **Compare**: `sa eval-compare --baseline env:production --candidate pack`. Review every added, removed and
   changed finding and every newly flagged candidate.
6. **Approve**: a reviewer other than the author sets `status: approved` and `approved_by`.
7. **Release**: `sa knowledge release --by <you>` — re-runs the eval gate and writes an immutable,
   checksummed snapshot to `knowledge/releases/<version>/`.
8. **Promote**: `sa knowledge promote <version> --env staging|production --by <you> --reason "..."` — re-runs the
   gate against the release and records the promotion in `deployments.yaml`.
9. **Roll back** if results deteriorate: `sa knowledge rollback --env production --by <you> --reason "..."`.

`--skip-eval` exists for bootstrapping and is recorded in history; do not use it for routine changes.

## Writing good records

### Synonyms

- Use `equivalent_terminology` only when the terms name the *same* function in the stated contexts.
  Use `closely_related` otherwise; the engine will show such matches but never count them.
- Scope with `contexts`. A variant can carry its own `contexts`; `exclusions` remove a term in specific contexts
  (e.g. `CSM` means Certified ScrumMaster in project management).
- Record `ambiguities` — they are shown to reviewers next to any proposed rule change.
- `constraint` must say what the term does **not** prove. Synonyms improve recognition; they do not establish competence.

### Equivalencies

- Target a capability (`skill.*`), never a `regulated_credential` (validation rejects it).
- Write indicators as groups of terms that must co-occur **in one sentence** (`all_of`). Prefer action + object
  pairs (`[led, coordinated] × [outage, crisis]`) over single words.
- Make leadership or ownership a `required_indicator` when the requirement is about leading, not participating.
- Always add `disqualifying_terms` for participation-only language (`participated`, `attended`, `drill`, `shadowed`).
- Set `min_months` and `min_indicators` conservatively; tighten rather than loosen when unsure.
- `validation_steps` are passed verbatim to the recruiter as "what to verify next". Make them concrete.
- `non_equivalencies` and `limitations` are required. If you cannot name what is *not* equivalent, the record is not ready.

### Skills and combinations

- `kind` matters: `tool` and `credential` can stand in for a capability they `support` when the requirement
  accepts alternatives; component `skill`s cannot (one component is partial evidence).
- `not_equivalent` relationships are explicit guardrails (help-desk ≠ incident management).
- Combinations need every component evidenced separately and are used only when the role states the
  supported capability and accepts alternatives.

## General knowledge vs. employer policy

If one employer disagrees with a general equivalency, do **not** edit the general record — add it to that
employer's `rejected_equivalencies` in `policy.yaml`. If an employer has validated an equivalency for their
roles, record it in `accepted_equivalencies` with who approved it.
