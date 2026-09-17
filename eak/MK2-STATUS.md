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
- CI now runs on `main`, `dev`, and all `eak/**` branches and installs the security extra.
- Dependency consistency (`pip check`) is a required gate.

## Architectural invariants preserved

1. No `if domain == medical/legal/aec` branches in Kernel Core.
2. Secrets enter through resolver boundaries, not execution snapshots.
3. Artifact access always includes tenant identity.
4. Human approval is bound to an authenticated principal and role evidence.
5. Work execution is at-least-once; providers with side effects remain responsible for idempotency keys declared by the ExecutionGraph.
6. Durable stores remain replaceable adapters; SQLite is the reference/local backend, not a distributed production database claim.

## Remaining production gates

Managed KMS/secrets, object storage, database and queue adapters; SBOM/vulnerability gates; deployment manifests; backup/restore drills; SLO/error-budget definitions; incident-response exercises; and end-to-end production-like validation.
