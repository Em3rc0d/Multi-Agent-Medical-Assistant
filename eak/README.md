# EAK workspace

`eak/` contains the active **Expert Agent Kernel** engineering line. The repository-root medical application remains preserved as Quarry #001: a source of real implementation evidence, not the definition of the kernel.

## Architecture rule

EAK is a domain-agnostic execution and trust kernel for verifiable expert systems. Domain knowledge must not leak into Kernel Core. Medical, AEC and Legal must compile through the same capability, provider, workflow, policy, evidence, evaluation and standards-governance contracts.

## Layout

- `kernel/` — domain-agnostic contracts, graph compilation, resolution, execution, trust, persistence, readiness and standards evidence gates.
- `providers/` — reusable provider adapters extracted from Quarry implementations.
- `runtimes/` — runtime adapters; runtime-native objects never become EAK contracts.
- `domains/medical/` — first executable Quarry-backed Domain Pack.
- `domains/aec/` and `domains/legal/` — cross-domain conformance packs that prevent false generalization.
- `governance/` — versioned standards registry, claim semantics, evidence profiles and standards watchlist.
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
MK7  standards governance            ACTIVE / MACHINE-VERIFIABLE BASELINE
```

## Current trust/runtime baseline

The engineering baseline includes tenant-aware policy/approval boundaries, durable work delivery with retries and idempotency requirements, durable EvidenceGraph and audit persistence, tamper-evident event chains, encrypted artifact adapters, snapshot integrity manifests, metadata-only telemetry, dependency auditing, CycloneDX SBOMs and fail-closed deployment readiness checks.

Reference SQLite and local-filesystem adapters remain explicitly **reference/local backends**. They are not a production deployment claim.

## Standards governance

`governance/standards-registry.json` is the canonical versioned catalogue for AI governance, cybersecurity, privacy, secure development, software quality, provenance, observability, software supply chain, agent interoperability and domain interoperability.

`StandardsGate` resolves additive profiles such as `platform.baseline`, `interop.agents`, `domain.medical`, `domain.aec` and `domain.legal` into required evidence families and fails closed when evidence is missing. Internal PASS means only that EAK has the required evidence for the mapped scope; it does not create ISO certification, regulatory approval, clinical validation or jurisdiction-specific legal compliance.

## Conformance

```bash
cd eak/kernel
python -m pip install -e '.[test,langgraph,security,observability]'
pytest
eak-conformance --root .
```

Packaging is separately validated by CI: kernel, providers and Medical Domain Pack must build valid wheels/sdists and install into a clean virtual environment. Standards governance has its own CI gate so registry changes cannot bypass profile/schema validation.

## Production boundary

`eak-readiness --profile <profile.json>` fails closed when a deployment lacks managed identity, managed secrets/KMS, managed artifact/database/queue infrastructure, current restore-drill evidence, SLO ownership, tenant-isolation evidence or a provider-certification profile.

Passing static readiness and standards gates is necessary, not sufficient. Real production requires environment-specific deployment evidence, applicable jurisdiction profiles, external attestations where required and operational ownership.

See `kernel/ROADMAP.md`, `kernel/OPERATIONS.md`, `kernel/RUNBOOK.md` and `governance/README.md` before introducing external I/O, sensitive artifacts, side-effecting providers or compliance claims.
