# ATS integration contract

The MVP works from exports. A connector for a specific ATS must produce the same data contracts and respect
the rules below. The ATS remains the system of record.

## What a connector supplies

| Contract | Source in the ATS | Notes |
|---|---|---|
| `requisition` | Job/requisition record, posted description, requirements, knockout questions, filters, scoring criteria | Set `inputs_received.screening_configuration` to `ats_api_verified` only when rules were read from the live configuration. |
| `candidates` | Application stage, disposition, the rule that excluded the applicant (if recorded), knockout answers, résumé-derived experience | De-identified. No names, contact details, photos or protected characteristics — the schema rejects them. |
| `outcomes` | Stage progression and recruiter activity for the measurement periods | Aggregate counts plus per-candidate review records for surfaced candidates. |

`sa schema <name>` prints each contract; `sa check <contract> <file>` validates a file.

## Permissions

| Permission | Required | Default |
|---|---|---|
| Read requisitions and screening configuration | Yes | — |
| Read candidate application data for selected requisitions | Only for candidate-pool assurance | Off until authorized per requisition |
| Write review lists (tags / saved searches) | Optional | Off |
| Write screening configuration | **Never automatic.** At most, create a draft change that an ATS administrator applies. | Off |

## Identifiers

Connectors map ATS requisition and application ids to opaque ids (`REQ-…`, `C-…`). The mapping table lives in
the employer's environment, not in Screening Assurance outputs.

## Approval requirements

- Any write requires an accepted finding in `decisions.yaml` with a named decider and rationale.
- Candidate review lists require an `approved_candidate_review` decision.

## Audit events

Every run records: requisition id, knowledge fingerprint, engine version, inputs received, run time.
Every decision records: finding id, disposition, rationale, decider, timestamp. Knowledge promotions and
rollbacks are recorded in `knowledge/deployments.yaml`. Connectors must additionally log every read of
candidate data (who, which requisition, when) and every write.

## Retention and deletion

- `candidates.authorization.retention_days` is mandatory. Candidate evidence and derived findings are deleted
  after that period; aggregate metrics may be retained.
- Deletion requests from the employer remove candidate evidence and candidate-level findings for the stated ids.

## Disclosure

If the ATS does not expose its actual screening configuration, the connector sets
`screening_configuration: recruiter_documentation` (or `not_supplied`) and the report states the limitation
rather than claiming a complete audit. Exclusions that the supplied rules cannot explain are reported as an
input limitation.
