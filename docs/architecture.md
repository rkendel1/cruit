# Architecture

Screening Assurance is a deterministic pipeline over three separate kinds of input, kept apart on purpose
(blueprint §6.5):

| Input | Owner | Contract |
|---|---|---|
| **General knowledge** — terminology, skills, transferable evidence | Knowledge administrators | `synonyms`, `skills`, `equivalencies` (+ `manifest`) |
| **Employer policy** — non-negotiables, accepted / rejected equivalencies | Employer | `policy` |
| **Requisition configuration** — posted requirements and the screening rules actually applied | Employer's ATS / recruiter | `requisition` |

Optional inputs: authorized de-identified `candidates`, human `decisions`, observed `outcomes`.
General knowledge never silently overrides employer policy: policy rejections suppress an equivalency (and
the report says so), and policy non-negotiables make a requirement *protected*.

## Data flow

```
requisition.yaml ─┐
policy.yaml ──────┤                 ┌── design findings + simulation patches ──┐
knowledge pack ───┼─► interpret ─► checks                                      ├─► explain ─► report.md / report.html
candidates.yaml ──┤                 └── rules ─► candidate assessment ─────────┘            findings.json / changes.yaml
decisions.yaml ───┤  (classification decisions feed back; rejected findings withdraw their patches)
outcomes.yaml ────┘─────────────────────────────────────────────► measure (Level 3)
```

## Engine stages (blueprint §7)

1. **Normalize** — `text.py`, `engine/interpret.py`. Candidate evidence is split into entries (experience,
   skills, credentials, learning, education) and sentences, each with a source locator such as
   `candidate:C-103/experience[0].s2`. Original text is preserved for every conclusion.
2. **Interpret** — `KnowledgePack.term_entries()` builds a context-aware term index for the requisition's job
   family (applying record contexts, variant contexts and exclusions; only `approved` records). Requirements
   and rules are mapped to concepts. `closely_related` terminology is kept separate: it is shown, never counted.
3. **Evaluate** — `engine/checks.py` runs deterministic checks per rule and per requirement. Where a finding
   implies a configuration correction it emits a *patch* (e.g. `{"years": 5}`, `{"add_terms": [...]}`,
   `{"removed": true}`). `engine/rules.py` simulates every rule against every candidate under the current
   logic, under all active patches, and under each patch alone. This yields, per finding, which candidates the
   correction alone would let through, and per candidate, which findings are responsible for unlocking them.
   `engine/candidates.py` then assesses evidence for each requirement: direct, terminology variant, supporting
   tool/credential, employer-permitted equivalency, or skill combination — with duration checks.
4. **Explain** — every finding is a `Finding` with the fields in blueprint §7 stage 4, plus affected and
   unlocked candidates and the simulation patch.
5. **Measure** — `measure.py` turns `outcomes.yaml` into measured metrics, separately labelled estimates,
   per-correction attribution, and one Level 3 finding.

## Candidate rediscovery and the workbench

`engine/discovery.py` groups current applicants and an authorized `candidate_pool` by the evidence supporting
review, reusing the requirement-evidence logic and the diagnostic run's rule simulation. The local workbench
(`workbench/`) orchestrates sessions, runs, decisions, exports, retention and reproducibility verification over
the same engine; see [workbench.md](workbench.md).

## Determinism and reproducibility

- No randomness, no network, no language model in the decision path. The same inputs and knowledge version
  produce byte-identical results (tested).
- Every finding records the knowledge **fingerprint** `pack@version+sha256[:10]`, computed from the content
  of the three documents, so an edited-but-not-re-versioned pack is detectable.
- Finding ids hash `(requisition, check, rule/requirement/candidate)` — not the knowledge version — so
  recorded human decisions remain attached when the knowledge changes.
- Releases are immutable snapshots with checksums; promotion refuses a tampered snapshot.

## Human authority

- The engine never writes to requisition or ATS configuration; tests assert the input is unchanged.
- Decisions are applied at load time:
  - `rejected` / `confirmed_necessary` withdraw that finding's patch, so candidates it alone unlocked are no
    longer surfaced;
  - `reclassified_preferred` / `confirmed_necessary` on an *unverified requirement* change how that requirement
    is treated in the next run (Step 2 → Step 3 feedback). The original finding stays, carrying the decision.
- `changes.yaml` lists only accepted findings unless `--include-pending` is passed.

## Extension points

- **Language-model assistance** (blueprint §7 stage 2) belongs in a pre-processing step that *proposes*
  structured candidate evidence or requirement concepts; outputs must be stored as hypotheses with provenance
  and pass through the same deterministic checks. It is intentionally absent from this milestone.
- **ATS connectors** produce the same `requisition` / `candidates` contracts; see
  [integration-contract.md](integration-contract.md).
- **New checks** are functions in `checks.py` that append `Finding`s and optional patches; add an eval case
  with expected and forbidden findings for each.
- **Knowledge storage** can move from YAML in git to a service without engine changes: the engine only uses
  `KnowledgePack`.

## Module map

| Module | Responsibility |
|---|---|
| `contracts.py` | Schema registry, YAML loading (dates kept as strings), prohibited-field screening |
| `knowledge/pack.py` | Pack model, fingerprint, context-aware term index, lookups |
| `knowledge/validate.py` | Referential integrity, regulated-credential guard, term-collision detection |
| `knowledge/diff.py` | Record-level diff with version-bump warnings |
| `knowledge/registry.py` | Releases, environments, promotion history, rollback, proposals |
| `engine/interpret.py` | Context, concept resolution, candidate evidence and equivalency matching |
| `engine/checks.py` | Design checks and requirement classification |
| `engine/rules.py` | Rule simulation and patch merging |
| `engine/candidates.py` | Requirement evidence, surfacing criteria, candidate-review findings |
| `engine/engine.py` | Orchestration, decisions, limitations |
| `measure.py` | Measured vs. estimated value, attribution, Level 3 |
| `report/` | Markdown, HTML (decision capture), change proposals, portfolio |
| `evals/harness.py` | Suite metrics, guardrails, version comparison and regression gate |
