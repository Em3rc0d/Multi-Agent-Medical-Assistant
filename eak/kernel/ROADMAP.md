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

Status: **ACTIVE**.

Implemented foundations: EvidenceGraph + PROV-compatible export, durable SQLite evidence persistence, authenticated approval contracts + durable decision store, append-only execution event persistence, content-off telemetry and evaluation gates.

## MK4 — Provider ecosystem

Status: **ACTIVE**.

Incubated provider boundaries exist for Docling, Qdrant, Tavily and PyTorch. MCP/A2A adapters and provider certification automation remain open.

## MK5 — Domain packs

Status: **ACTIVE**.

Medical is the first executable Domain Pack. AEC and Legal manifests participate in the same contract/conformance model and remain intentionally thin until their real providers are introduced.

## MK6 — Production hardening

Status: **ACTIVE**.

Implemented foundations: RBAC/tenant enforcement primitives, secret references/resolvers, tenant-isolated encrypted local artifact storage, durable SQLite event/evidence/approval stores, durable work queue with leases/retries, CI across Python 3.11–3.13, and dependency consistency checks.

Still open before a production claim: managed identity integration, external KMS/secret manager adapters, managed object storage/database backends, distributed queue/worker deployment, supply-chain vulnerability/SBOM gates, backup/restore drills, SLOs, deployment environments and incident-response validation.
