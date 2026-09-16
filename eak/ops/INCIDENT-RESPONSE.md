# Incident Response Runbook

## Scope

Use this runbook for suspected data exposure, cross-tenant access, compromised credentials/providers, corrupted evidence/artifacts, unauthorized side effects, or loss of execution/audit integrity.

## Severity

- **SEV-1:** confirmed or credible cross-tenant/data-security compromise, unsafe high-risk side effect, or integrity loss affecting trusted artifacts.
- **SEV-2:** material service degradation, provider compromise contained before protected data/side effects, or partial audit/recovery impairment.
- **SEV-3:** bounded defect with no protected-data exposure, unsafe side effect, or material integrity loss.

## Response sequence

1. **Declare and timestamp.** Assign incident ID, commander, technical owner, and recorder.
2. **Contain.** Disable affected provider/capability, revoke credentials where applicable, stop side-effecting workflows, and preserve unaffected service boundaries.
3. **Preserve evidence.** Snapshot relevant immutable events, policy decisions, execution/provider versions, artifact hashes, and deployment metadata. Do not copy sensitive payloads into chat/tickets unless approved.
4. **Assess blast radius.** Identify tenants, executions, artifacts, providers, credentials, and time window potentially affected.
5. **Eradicate.** Patch/revoke/replace the compromised component and invalidate certifications/readiness where trust can no longer be established.
6. **Recover.** Restore from verified backups when needed, run integrity/conformance tests, re-establish provider readiness, and progressively re-enable workflows.
7. **Communicate.** Follow deployment-specific legal/security notification requirements and stakeholder routing.
8. **Review.** Produce a blameless timeline, root cause, control failures, corrective actions, owners, and deadlines.

## Required artifacts

The deployment should preserve incident ID, affected execution IDs, hashes rather than raw content where possible, policy/certification versions, mitigation actions, restore verification, and final closure decision.

## Verification gate

`incident_runbook_verified=true` may only be asserted after the deployment has assigned real owners/contacts and exercised this path in a tabletop or real incident. Documentation existence alone is insufficient.
