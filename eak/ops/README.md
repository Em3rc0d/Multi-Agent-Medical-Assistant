# EAK Operations

Operational documents in this directory define the evidence required to operate an EAK deployment. They do **not** make a deployment production-ready by existing in Git.

A production deployment must bind these generic runbooks to concrete infrastructure, owners, alert routes, backup systems, secrets/key managers, and measured recovery/SLO evidence. `ProductionReadinessGate` remains fail-closed until those deployment facts are explicitly verified.

## Required operational evidence

- `INCIDENT-RESPONSE.md`: severity model, containment, evidence preservation, recovery, and post-incident process.
- `DISASTER-RECOVERY.md`: backup/restore procedure plus measured RPO/RTO from a restore drill.
- `SLO.md`: service-level indicators/objectives and actionable alerts.

## Rule

Do not set readiness evidence to `true` from documentation review alone. Verification must come from the target deployment (successful restore drill, configured alert test, dependency scan result, and exercised incident path).
