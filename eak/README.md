# EAK workspace

`eak/` contains the active Expert Agent Kernel engineering line. The repository-root medical application is preserved separately as Quarry #001.

## Layout

- `kernel/` — the domain-agnostic contract, compilation, resolution, execution and trust layer.
- `providers/` — reusable provider adapters extracted from Quarry implementations.
- `runtimes/` — execution-runtime adapters; runtime-native objects never become EAK contracts.
- `domains/medical/` — first Quarry-backed Domain Pack.
- `domains/aec/` and `domains/legal/` — cross-domain conformance packs used to prevent false generalization.
- `ci/` — conformance material.
- `artifacts/` — frozen engineering evidence and handoff snapshots.

## Milestone state

```text
MK0  architecture/specification      CLOSED / FROZEN
MK1  contract-first kernel           CLOSED
MK2  controlled extraction           ACTIVE
MK3  trust/evidence runtime          ACTIVE
MK4  provider ecosystem              PARTIAL
MK5  domain packs                    PARTIAL
MK6  production hardening            BLOCKED BY EXTERNAL INFRASTRUCTURE
```

Read `kernel/ROADMAP.md` for exit gates and `kernel/SECURITY.md` before introducing any provider with external I/O, sensitive artifacts or side effects.

## Conformance

The architectural acceptance test is not "many agents". It is that Medical, AEC and Legal can use the same kernel compiler/resolver/policy contracts without a domain switch in Kernel Core.

```bash
cd eak/kernel
python -m pip install -e '.[test,langgraph]'
pytest
eak-conformance --root .
```

## Production boundary

Reference SQLite/filesystem/native adapters are intentionally tagged `local-durable`. They can satisfy the engineering readiness profile but **must fail** the production readiness profile. Production readiness requires external production-tier identity, storage, eventing, evidence, secrets, telemetry and operational infrastructure.
