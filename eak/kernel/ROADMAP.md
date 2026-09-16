# EAK Engineering Roadmap

## MK0 — Architecture mining and specification

Status: FROZEN for engineering incubation.

## MK1 — Contract-first kernel

Status: ACTIVE.

Exit gates:

- Schema and semantic conformance across Medical, AEC, and Legal.
- Deterministic fail-closed provider resolution.
- Policy and certification boundaries.
- Execution snapshots and lifecycle state machine.
- At least one real runtime adapter with pause/resume integration tests.
- No domain switch in Kernel Core.

## MK2 — Quarry #001 controlled extraction

Blocked until MK1 exits. Candidate extractions are generic document parsing, retrieval, reranking, model-provider boundaries, and artifact handling. Medical semantics remain in `domain-medical`.

## MK3 — Trust and evidence runtime

EvidenceGraph persistence, W3C PROV export, claim assessment, approval identity, audit trail, and OpenTelemetry integration.

## MK4 — Provider ecosystem

Docling, Qdrant, web-search, PyTorch/vision, MCP and A2A adapters with certification profiles.

## MK5 — Domain packs

Medical first, AEC second, Legal third. Each must use the same kernel APIs and conformance harness.

## MK6 — Production hardening

RBAC, secrets, tenant isolation, encrypted artifact storage, queues/workers, durable event store, deployment, supply-chain security, dependency scanning, and disaster-recovery procedures.
