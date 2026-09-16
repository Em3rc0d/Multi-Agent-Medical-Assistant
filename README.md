# Expert Agent Kernel (EAK)

This repository is the engineering home of **EAK — Expert Agent Kernel**, a domain-agnostic execution and trust kernel for building verifiable expert systems from versioned capabilities, providers, artifacts, workflows, evidence, policy and evaluations.

The repository began as a fork of [`souvikmajumder26/Multi-Agent-Medical-Assistant`](https://github.com/souvikmajumder26/Multi-Agent-Medical-Assistant). The original medical application is intentionally retained as **Quarry #001**: a real implementation from which reusable capabilities and domain-specific behavior are being separated. See [`UPSTREAM.md`](UPSTREAM.md) for provenance and attribution.

> **Engineering status:** EAK is an engineering/research project. It is not, by itself, a medical device, legal authority, structural-analysis product, autonomous decision maker, or production certification.

## Project thesis

EAK is designed around one invariant:

> **A new Domain Pack must not require a Kernel Core change.**

The system is modeled as:

```text
Expert System
=
Kernel
+ Domain Pack
+ Capability Set
+ Certified Providers
+ Knowledge
+ Policies
+ Evaluation Profiles
```

A workflow resolves abstract capabilities to concrete providers, executes them through a runtime adapter, records artifacts and evidence, applies policy and human-approval gates where required, and produces auditable outputs.

## Nine root contracts

EAK Core Spec v0.2 defines nine root contracts:

1. `Capability` — what the system can do.
2. `Provider` — how a capability is implemented.
3. `Artifact` — versioned, integrity-addressed inputs and outputs.
4. `DomainPack` — domain semantics, policies, knowledge and evaluations.
5. `ExecutionContext` — the immutable execution snapshot and security context.
6. `Workflow / ExecutionGraph` — logical plan and resolved physical plan.
7. `Claim / EvidenceGraph` — what the system asserts and the provenance behind it.
8. `Policy` — authorization, safety, data and workflow constraints.
9. `Evaluation / Certification` — measurable gates for deployment eligibility.

Agents are one possible provider kind, not the architecture's fundamental unit. Deterministic tools, retrievers, ML models, external services, humans and subworkflows can satisfy capabilities as well.

## Repository map

```text
.
├── eak/
│   ├── kernel/          # domain-agnostic contracts, compiler, resolver and trust runtime
│   ├── providers/       # generic provider adapters extracted from Quarry #001
│   ├── runtimes/        # runtime adapters such as LangGraph
│   ├── domains/
│   │   ├── medical/     # first Quarry-backed Domain Pack
│   │   ├── aec/         # cross-domain conformance pack
│   │   └── legal/       # cross-domain conformance pack
│   ├── ci/              # conformance and validation material
│   └── artifacts/       # frozen engineering evidence / handoff material
│
├── agents/              # original medical application — Quarry #001
├── app.py               # original FastAPI medical application entry point
└── UPSTREAM.md           # fork provenance and attribution
```

The medical application at the repository root is preserved for extraction and comparison. New kernel semantics belong under `eak/`; medical-only semantics belong under `eak/domains/medical/`.

## Current engineering state

| Milestone | State |
|---|---|
| MK0 — architecture mining / Core Spec v0.2 | **CLOSED / FROZEN** |
| MK1 — contract-first kernel | **CLOSED** |
| MK2 — Quarry #001 controlled extraction | **ACTIVE** |
| MK3 — trust and evidence runtime | **ACTIVE** |
| MK4 — provider ecosystem | **PARTIAL** |
| MK5 — domain packs | **PARTIAL** |
| MK6 — production hardening | **BLOCKED BY EXTERNAL INFRASTRUCTURE** |

The current branch line includes generic Docling, Qdrant, Tavily and Torch provider boundaries; LangGraph lifecycle integration; cross-domain Medical/AEC/Legal conformance; tenant-scoped artifacts; durable local audit/evidence/approval stores; fail-closed policy boundaries; metadata-only telemetry; and explicit deployment-readiness tiers.

Local SQLite/filesystem/native adapters are **engineering reference implementations**, not production certification. `DeploymentProfile.PRODUCTION` intentionally rejects them until production-tier infrastructure adapters are supplied.

## Quick start — EAK kernel

Python 3.11+ is required.

```bash
cd eak/kernel
python -m pip install -e '.[test,langgraph]'
pytest

eak-conformance --root .
```

The CI matrix validates Python 3.11, 3.12 and 3.13, Draft 2020-12 schemas, kernel tests, provider boundaries, Domain Pack manifests, Quarry medical adapters and cross-domain compiler conformance.

## Architecture rules

```text
Capability describes WHAT; Provider describes HOW.
Domain knowledge never enters Kernel Core.
Runtime/framework state never becomes an EAK contract.
Claims and Evidence are distinct entities.
Policies and deployment readiness fail closed.
Secrets are referenced, never embedded in execution contracts.
Human authority is authenticated identity + role + policy, not free-form text.
```

See [`eak/kernel/README.md`](eak/kernel/README.md), [`eak/kernel/ROADMAP.md`](eak/kernel/ROADMAP.md), and [`eak/kernel/SECURITY.md`](eak/kernel/SECURITY.md) for the executable kernel baseline, milestone gates and security invariants.

## Quarry #001 — medical reference implementation

The upstream medical assistant remains available in this fork as a reference implementation for controlled extraction. It contains FastAPI, LangGraph, RAG/Qdrant, Docling, web search and medical-image components. Its historical behavior and claims must not be confused with EAK's current trust model or production-readiness gates.

No EAK component should be presented as autonomous diagnosis or as a substitute for qualified professional review.

## License and provenance

This fork retains the upstream Apache License 2.0. Upstream source, notices and provenance are documented in [`UPSTREAM.md`](UPSTREAM.md). New EAK code in this fork is distributed under the repository's Apache-2.0 license unless a file states otherwise.
