# MK2 / MK3 Status

Status: **ACTIVE — controlled extraction + trust hardening**

## Landed boundaries

- generic Docling, Qdrant, Tavily and Torch provider packages extracted from Quarry #001;
- medical-specific adapters isolated under `domains/medical`;
- tenant-scoped content-addressed artifact store;
- durable SQLite event store with per-execution tamper-evident hash chains;
- durable authenticated approval records;
- durable evidence-graph snapshots with integrity verification;
- metadata-only durable telemetry sink;
- opaque `secret://` references and pluggable secret resolution;
- explicit deployment-readiness profiles that distinguish engineering adapters from production adapters.

## Important non-claim

The local filesystem and SQLite implementations are **reference engineering adapters**, not production certification. `DeploymentProfile.PRODUCTION` intentionally rejects them. Production remains blocked until external production-tier implementations are supplied for eventing, artifacts, policy, telemetry, approvals and evidence storage.

## Next gates

1. finish Quarry #001 migration of remaining reusable document/retrieval boundaries;
2. add production adapters behind the existing interfaces;
3. add RBAC/tenant identity integration and external secret-manager adapters;
4. add OpenTelemetry exporter integration and supply-chain/dependency security gates;
5. run full Medical Domain Pack workflow through the hardened trust runtime.
