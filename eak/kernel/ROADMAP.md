# EAK Engineering Roadmap

## MK0 — Architecture mining and specification

Status: **CLOSED / FROZEN**.

## MK1 — Contract-first kernel

Status: **CLOSED**.

Exit gates passed: schema + semantic conformance across Medical/AEC/Legal, deterministic fail-closed provider resolution, policy/certification boundaries, execution snapshots/state machine, real LangGraph pause/resume integration, and no domain switch in Kernel Core.

## MK2 — Quarry #001 controlled extraction

Status: **ACTIVE**.

Generic Docling, Qdrant, Tavily and Torch provider boundaries have been extracted. Medical semantics remain isolated in `domains/medical`. Remaining work is to complete reusable document/retrieval migration without importing Quarry-specific orchestration into the kernel.

## MK3 — Trust and evidence runtime

Status: **ACTIVE**.

Landed: tenant-scoped artifacts, durable/tamper-evident local eventing, durable approval records, evidence-graph persistence, metadata-only telemetry, secret references, and deployment-readiness gates. Remaining: production-tier persistence, external identity/RBAC integration, OpenTelemetry export, stronger claim assessment and operational audit tooling.

## MK4 — Provider ecosystem

Status: **PARTIAL**.

Docling, Qdrant, Tavily and Torch adapters exist. MCP and A2A adapters plus formal certification profiles remain open.

## MK5 — Domain packs

Status: **PARTIAL**.

Medical is the first executable Quarry-backed pack. AEC and Legal remain conformance packs until they gain real provider implementations. All must continue to use the same kernel APIs.

## MK6 — Production hardening

Status: **BLOCKED BY EXTERNAL INFRASTRUCTURE**.

Required before any production claim: production RBAC/identity, external secrets manager, tenant isolation backed by production storage, encrypted artifact service, distributed queue/workers, production event/evidence stores, OpenTelemetry backend, deployment/rollback automation, supply-chain security, dependency scanning, backup/restore and disaster-recovery evidence.
