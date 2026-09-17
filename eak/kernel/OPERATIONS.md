# EAK Operations Baseline

This document defines the minimum operational contract for deployments of EAK. It does **not** claim that the reference SQLite/local-filesystem adapters are suitable for horizontally scaled production.

## Durable state

EAK separates four durable state classes:

- execution/audit events (`SQLiteEventStore` reference adapter),
- evidence graphs (`SQLiteEvidenceStore`),
- approval requests and immutable decisions (`SQLiteApprovalStore`),
- queued node work (`SQLiteWorkQueue`).

Artifact bytes are stored behind the `ArtifactStore` boundary. `EncryptedLocalArtifactStore` is a single-host encrypted reference backend; production deployments should replace it with tenant-isolated managed object storage plus KMS-backed envelope encryption.

## Secrets

Configuration stores only references such as `secret://env/EAK_ARTIFACT_KEY`. Secret values are resolved at runtime and must not be copied into ExecutionContext, events, telemetry, claims or artifacts. Production deployments should provide a resolver backed by their secret manager/KMS.

## Backup and restore

For the reference single-host deployment:

1. Quiesce workers or stop new leases.
2. Use SQLite online backup or filesystem snapshots for event/evidence/approval/work databases.
3. Snapshot the encrypted artifact root in the same consistency window.
4. Store encryption keys separately from artifact backups.
5. Restore into an isolated environment first and run integrity/conformance checks before reopening traffic.

A production environment must automate this process and perform scheduled restore drills. A backup that has not been restored successfully is not considered verified.

## Failure semantics

Worker delivery is at-least-once. A lease can expire and be delivered again. Side-effecting providers therefore require idempotency keys at the provider boundary. Exhausted work moves to `DEAD` rather than being silently discarded.

Approval decisions are immutable. Evidence-node identifiers are collision checked. Artifact reads verify plaintext SHA-256 after decryption.

## Observability

Telemetry is content-off by default. Record identifiers, hashes, status, latency and bounded metadata; do not capture prompts, medical/legal documents, images or outputs unless an explicit data policy authorizes content capture.

## Production replacement points

Before horizontal production deployment replace or validate:

- SQLite stores -> managed transactional database/event store,
- SQLiteWorkQueue -> distributed queue with equivalent lease/idempotency semantics,
- EncryptedLocalArtifactStore -> object storage + KMS,
- EnvironmentSecretResolver -> managed secret manager,
- local identity dictionaries -> verified OIDC/workload identity,
- in-memory telemetry -> OpenTelemetry exporter/collector.

## Readiness rule

A deployment is not `PRODUCTION` merely because tests pass. It must have environment-specific policy, certified providers, restore-tested durable stores, monitored SLOs, secrets/KMS integration, tenant-isolation tests, and an incident-response owner.
