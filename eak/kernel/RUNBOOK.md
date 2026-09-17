# EAK Incident and Recovery Runbook

This runbook is the reference operational procedure. Environment-specific deployments must replace placeholders with real owners, endpoints and escalation paths.

## Severity model

- SEV-1: cross-tenant exposure, unauthorized provider action, corrupted evidence/audit state, or widespread outage.
- SEV-2: degraded execution, queue backlog threatening SLOs, provider outage with no acceptable fallback.
- SEV-3: isolated workflow/provider failure with bounded impact.

## Immediate containment

For a suspected tenant/security incident: stop new work admission, revoke or disable affected provider credentials, preserve append-only audit/evidence stores, and do not delete potentially relevant execution records. For provider instability: disable the provider in registry/readiness state so fail-closed resolution excludes it.

## Recovery order

1. Establish incident owner and timestamp.
2. Freeze affected provider/workflow versions.
3. Verify tenant and policy boundaries.
4. Restore durable stores only from a restore-tested backup set.
5. Verify artifact integrity hashes and decryption.
6. Run schema, semantic, cross-domain and tenant-isolation conformance.
7. Resume workers with bounded concurrency.
8. Monitor queue depth, failure rate, latency and policy denials.
9. Close only after evidence/audit continuity is verified.

## Queue recovery

Delivery is at-least-once. Expired leases may be delivered again. Do not replay side-effecting work unless an idempotency key exists and the provider honors it. `DEAD` work requires explicit operator disposition; it is never silently dropped.

## Evidence and approvals

Approval decisions are immutable. Evidence identifiers are collision-checked. If evidence or approval persistence is unavailable, workflows requiring them must fail closed rather than continue without provenance or authority.

## Production readiness gate

Use `eak-readiness --profile <profile.json>`. A non-zero result blocks a production claim. Passing the static checker is necessary but not sufficient: deployment-specific smoke tests, restore drills, identity/KMS validation, provider certification and monitoring must also pass.
