# EAK Engineering Roadmap

## MK0 — Architecture mining and specification

Status: **FROZEN / CLOSED** for engineering incubation.

## MK1 — Contract-first kernel

Status: **CLOSED**.

Exit gates are green: schema and semantic conformance across Medical/AEC/Legal, deterministic fail-closed resolution, policy/certification boundaries, execution snapshots/lifecycle, LangGraph pause/resume integration, and no domain switch in Kernel Core.

## MK2 — Quarry #001 controlled extraction

Status: **ACTIVE / SUBSTANTIALLY EXTRACTED**.

Generic document parsing, Qdrant retrieval, Tavily search, PyTorch boundaries and medical adapters have been separated into provider/domain packages. Remaining work is migration of legacy application entrypoints away from direct agent coupling.

## MK3 — Trust and evidence runtime

Status: **ACTIVE / FOUNDATION DURABLE**.

EvidenceGraph + PROV-compatible export, durable evidence persistence, authenticated approval contracts + immutable decisions, append-only execution audit events, metadata-only telemetry, and evaluation gates exist. Distributed/managed backends remain deployment work.

## MK4 — Provider ecosystem

Status: **ACTIVE**.

Incubated provider boundaries exist for Docling, Qdrant, Tavily and PyTorch. Durable invocation workers now bridge frozen provider selections to at-least-once execution with audit events and idempotency enforcement. MCP/A2A adapters and automated provider certification remain open.

## MK5 — Domain packs

Status: **ACTIVE**.

Medical is the first executable Domain Pack. AEC and Legal manifests participate in the same contract/conformance model and remain intentionally thin until their real providers are introduced.

## MK6 — Production hardening

Status: **ACTIVE / AUTOMATABLE BASELINE IMPLEMENTED**.

Implemented foundations: RBAC/tenant enforcement primitives, secret references/resolvers, tenant-isolated encrypted local artifact storage, durable event/evidence/approval stores, durable work queue with leases/retries, OpenTelemetry boundary, Python 3.11–3.13 CI, dependency audit, CycloneDX SBOM generation, operations/runbook docs, and fail-closed deployment readiness checks.

Still open before a production claim because they require a real target environment: managed identity, external KMS/secret manager, managed object/database/queue backends, restore drill evidence, deployed SLO monitoring, incident-response ownership and end-to-end production-like validation.
