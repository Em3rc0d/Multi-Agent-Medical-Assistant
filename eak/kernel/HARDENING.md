# EAK Production Hardening

EAK does not use "production ready" as a documentation label. Production readiness is a set of executable gates with deployment-specific evidence.

## Security boundary

- Authentication happens outside the kernel; EAK consumes an authenticated `Principal`.
- Authorization is fail-closed and tenant-scoped.
- Cross-tenant access requires an explicit cross-tenant role with an explicit action grant.
- Secret values are resolved behind a `SecretProvider`; contracts and Domain Packs carry references, not credentials.
- Secret objects redact their value from `str()` and `repr()`; revealing a value is an explicit operation.
- Sensitive artifact bytes may be wrapped with authenticated AES-GCM encryption before crossing an `ArtifactStore` boundary.
- Telemetry is metadata-first and rejects prompt/document/raw-output fields by default.

## Durability boundary

- Execution events have a durable SQLite reference backend with WAL, FULL synchronous mode, integrity checks, and consistent online backup.
- Worker tasks have a durable SQLite reference queue with leases, bounded attempts, retry delay, lease ownership enforcement, and stale-lease reclamation.
- SQLite is the local/reference implementation. Horizontally scaled deployments replace it behind the same semantics with a managed database/broker.

## Artifact boundary

- Local storage is content addressed by SHA-256 and partitioned by tenant.
- Writes are atomic and best-effort private on POSIX-like systems.
- Reads revalidate content digests.
- The local backend is never exposed as a raw static directory.
- Production deployments should use an encrypted object-store adapter plus managed key service; the kernel encryption wrapper remains useful for application-level encryption where required.

## Recovery boundary

- Backups must be created from consistent backend snapshots, not copied from live database files ad hoc.
- Snapshot manifests contain relative paths, sizes, and SHA-256 digests.
- Restore procedures must verify manifests before a restored environment can become ready.
- Deployment runbooks must define tested RPO/RTO values; EAK core does not invent those values.

## Scale boundary

The SQLite backends are deliberately bounded reference implementations. A deployment that requires multiple workers/hosts must supply production adapters for event persistence, work queues, artifact storage, secrets, and telemetry. Domain and workflow contracts must remain unchanged when those adapters are swapped.

## Release gate

A release candidate is blocked if any of the following is true:

1. schema/conformance tests fail;
2. any supported Python version fails;
3. provider/domain package tests fail;
4. hardening/security boundary tests fail;
5. a required provider is uncertified or not ready;
6. recovery verification fails;
7. a deployment requires an adapter that only has a reference/local implementation.

This file defines engineering gates, not external medical, legal, safety, or regulatory certification.
