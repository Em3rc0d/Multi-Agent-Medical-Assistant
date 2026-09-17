# EAK MK2+ Hardening Status

Branch: `eak/mk2-production-hardening`

This phase turns the v0.2 contract-first baseline into an operationally credible kernel without changing the rule that domain semantics stay outside Kernel Core.

## Closed in this increment

- Secret references and runtime resolvers; secret values are not persisted by the kernel.
- Principal/tenant access primitive with fail-closed cross-tenant enforcement.
- Native policy tenant-match enforcement.
- Durable SQLite work queue with lease ownership, bounded retries, ACK/NACK and dead-letter state.
- Durable approval requests/immutable reviewer decisions.
- Durable EvidenceGraph persistence.
- Optional Fernet encrypted local artifact storage with per-tenant paths and content-integrity verification.
- Queue-to-provider worker bridge: durable `InvocationRequest` delivery, invoker dispatch, audit events, retries and side-effect idempotency enforcement.
- Optional OpenTelemetry metadata-only sink; content capture remains rejected by default.
- CI runs on `main`, `dev`, and all `eak/**` branches and installs security/observability extras.
- Dependency consistency (`pip check`) is required.
- Dedicated supply-chain workflow audits Python dependencies and emits a CycloneDX SBOM artifact.

## Architectural invariants preserved

1. No `if domain == medical/legal/aec` branches in Kernel Core.
2. Secrets enter through resolver boundaries, not execution snapshots.
3. Artifact access always includes tenant identity.
4. Human approval is bound to an authenticated principal and role evidence.
5. Work execution is at-least-once; side-effecting invocations require an idempotency key before queue admission.
6. Durable stores remain replaceable adapters; SQLite is the reference/local backend, not a distributed production database claim.
7. Telemetry is metadata-first and rejects prompt/document/content capture by default.

## Remaining production gates

Managed KMS/secrets, object storage, database and distributed queue adapters; deployment manifests; backup/restore drills; SLO/error-budget definitions; incident-response exercises; and end-to-end production-like validation.
