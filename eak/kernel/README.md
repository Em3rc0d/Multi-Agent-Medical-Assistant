# Expert Agent Kernel (EAK)

Status: **MK1 CLOSED / MK2–MK3 ACTIVE**

EAK is a domain-agnostic execution and trust kernel for building verifiable expert systems from versioned capabilities, providers, artifacts, workflows, evidence, policy and evaluations. Domain semantics stay outside Kernel Core.

## Current baseline

The same compiler and resolver support Medical, AEC and Legal conformance fixtures without `if domain == ...` in the core. LangGraph is a runtime adapter, not an EAK contract. Quarry #001 has already yielded generic provider boundaries plus a Medical Domain Pack adapter layer.

Trust/runtime reference implementations now include tenant-scoped content-addressed artifacts, SQLite event persistence with tamper-evident hash chains, authenticated approval persistence, evidence graph persistence, metadata-only telemetry, opaque secret references and explicit deployment-readiness profiles.

These local adapters are engineering references, **not a production certification**. The production readiness profile intentionally rejects SQLite/filesystem/native-local adapters until production-tier implementations are supplied.

## Run

```bash
python -m pip install -e '.[test,langgraph]'
pytest

eak-conformance --root .
```

## Core invariants

```text
A new Domain Pack MUST NOT require a Kernel Core change.
Capability describes WHAT; Provider describes HOW.
Claims and Evidence are distinct.
Policies and deployment gates fail closed.
Runtime/framework state never becomes an EAK contract.
```
