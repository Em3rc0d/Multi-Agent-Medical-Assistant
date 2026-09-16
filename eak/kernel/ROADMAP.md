# EAK Engineering Roadmap

## MK0 — Architecture mining and specification

Status: **CLOSED / FROZEN**.

The v0.2 contract set is the engineering baseline. Contract changes require an explicit compatibility decision rather than incidental runtime drift.

## MK1 — Contract-first kernel

Status: **CLOSED**.

Exit gates passed:

- Schema and semantic conformance across Medical, AEC, and Legal.
- Deterministic fail-closed provider resolution.
- Policy and certification boundaries.
- Execution snapshots and lifecycle state machine.
- LangGraph 1.2.x runtime adapter with pause/resume integration tests.
- Python 3.11, 3.12, and 3.13 CI.
- No domain switch in Kernel Core.

## MK2 — Quarry #001 controlled extraction

Status: **ACTIVE**.

Generic boundaries already extracted include artifact storage, provider interfaces, document/provider packaging, medical adapter seams, and cross-domain Domain Pack manifests. Remaining work must continue to move reusable behavior out of legacy `agents/` without moving medical semantics into Kernel Core.

Exit gates:

- Generic document parsing/retrieval/reranking providers are independently packaged.
- Medical-specific prompts, models, policies, and interpretation remain under `domain-medical`.
- Legacy runtime can be retired or isolated without breaking EAK conformance.
- No duplicated provider implementation exists in both legacy and EAK paths without an explicit migration owner.

## MK3 — Trust and evidence runtime

Status: **ACTIVE / PARTIAL**.

Implemented foundations include EvidenceGraph representation, PROV export boundary, claim/evaluation primitives, approval identity boundary, durable audit/event persistence, and metadata-first telemetry.

Exit gates:

- Durable EvidenceGraph persistence.
- Stable W3C PROV export fixtures.
- Claim assessment profiles and versioned evaluator evidence.
- Authenticated approval records tied to execution/node scope.
- OpenTelemetry adapter with sensitive content disabled by default.

## MK4 — Provider ecosystem

Status: **ACTIVE / PARTIAL**.

Current providers establish package boundaries and Quarry adapters. Planned production adapters include Docling, Qdrant, web search, PyTorch/vision, MCP, and A2A with explicit certification profiles.

Exit gates:

- Provider readiness/health contract.
- Versioned capability declarations and certification records.
- No provider credentials stored in Domain Packs or ExecutionContext.
- MCP/A2A remain protocol adapters, not kernel semantics.

## MK5 — Domain packs

Status: **ACTIVE / PARTIAL**.

Medical is the first executable Domain Pack; AEC and Legal remain conformance/reference packs until their real provider sets are implemented.

Exit gates:

- Medical executes through EAK APIs rather than legacy named-agent routing.
- AEC and Legal each execute at least one end-to-end workflow through the same kernel APIs.
- New domain installation requires no `if domain == ...` branch in Kernel Core.

## MK6 — Production hardening

Status: **ACTIVE**.

Implemented foundations include fail-closed tenant RBAC, explicit secret-provider boundaries, tenant-scoped content-addressed artifact storage, optional authenticated encryption, durable SQLite event persistence, durable leased work queues, recovery manifests, and CI across supported Python versions.

Remaining exit gates:

- Production secret backend adapter (cloud/Vault-class system) selected per deployment.
- Distributed queue/broker adapter for horizontally scaled workers.
- Encrypted production object storage adapter and key-rotation procedure.
- Supply-chain scanning, signed/reproducible release artifacts, and dependency policy.
- Deployment manifests and environment-specific configuration validation.
- Backup/restore drill with documented RPO/RTO targets.
- Operational SLOs, alerts, incident-response, and disaster-recovery runbooks.

Production is not declared complete until every remaining MK6 gate has executable evidence.
