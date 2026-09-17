# EAK workspace

`eak/` contains the active **Expert Agent Kernel** engineering line. The repository-root medical application remains preserved as Quarry #001: a source of real implementation evidence, not the definition of the kernel.

## Architecture rule

EAK is a domain-agnostic execution and trust kernel for verifiable expert systems. Domain knowledge must not leak into Kernel Core. Medical, AEC and Legal must compile through the same capability, provider, workflow, policy, evidence and evaluation contracts.

## Layout

- `kernel/` — domain-agnostic contracts, graph compilation, resolution, execution, trust, persistence and readiness gates.
- `providers/` — reusable provider adapters extracted from Quarry implementations.
- `runtimes/` — runtime adapters; runtime-native objects never become EAK contracts.
- `domains/medical/` — first executable Quarry-backed Domain Pack.
- `domains/aec/` and `domains/legal/` — cross-domain conformance packs that prevent false generalization.
- `deploy/` — reference and production deployment profiles.
- `artifacts/` — frozen engineering evidence and handoff snapshots.

## Milestone state

```text
MK0  architecture/specification      CLOSED / FROZEN
MK1  contract-first kernel           CLOSED
MK2  controlled extraction           ACTIVE / SUBSTANTIALLY EXTRACTED
MK3  trust/evidence runtime          ACTIVE / DURABLE FOUNDATION
MK4  provider ecosystem              ACTIVE
MK5  domain packs                    ACTIVE / MEDICAL FIRST
MK6  production hardening            AUTOMATABLE BASELINE IMPLEMENTED
                                      REAL ENVIRONMENT GATES OPEN
```

## Current trust/runtime baseline

The engineering baseline includes tenant-aware policy/approval boundaries, durable work delivery with retries and idempotency requirements, durable EvidenceGraph and audit persistence, tamper-evident event chains, encrypted artifact adapters, snapshot integrity manifests, metadata-only telemetry, dependency auditing, CycloneDX SBOMs and fail-closed deployment readiness checks.

Reference SQLite and local-filesystem adapters remain explicitly **reference/local backends**. They are not a production deployment claim.

## Conformance

```bash
cd eak/kernel
python -m pip install -e '.[test,langgraph,security,observability]'
pytest
eak-conformance --root .
```

Packaging is separately validated by CI: kernel, providers and Medical Domain Pack must build valid wheels/sdists and install into a clean virtual environment.

## Production boundary

`eak-readiness --profile <profile.json>` fails closed when a deployment lacks managed identity, managed secrets/KMS, managed artifact/database/queue infrastructure, current restore-drill evidence, SLO ownership, tenant-isolation evidence or a provider-certification profile.

Passing the static readiness checker is necessary, not sufficient. Real production requires environment-specific deployment evidence and operational ownership.

See `kernel/ROADMAP.md`, `kernel/OPERATIONS.md` and `kernel/RUNBOOK.md` before introducing external I/O, sensitive artifacts or side-effecting providers.
