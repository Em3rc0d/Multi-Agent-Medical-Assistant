# Upstream provenance

This repository is a fork of:

- **Upstream project:** `souvikmajumder26/Multi-Agent-Medical-Assistant`
- **Upstream URL:** https://github.com/souvikmajumder26/Multi-Agent-Medical-Assistant
- **Original project license:** Apache License 2.0

The upstream application and its historical assets remain valuable as **Quarry #001** for the EAK project. The fork preserves upstream history so original authorship can be inspected commit-by-commit.

## Fork direction

The active fork introduces **EAK — Expert Agent Kernel**, a domain-agnostic execution and trust architecture for verifiable expert systems. EAK-specific work lives primarily under `eak/` and is intentionally separated from the original medical application's domain behavior.

The fork does not claim that upstream medical behavior, models, data, prompts or documentation have been independently clinically validated. Historical upstream statements about diagnosis, confidence or production readiness must not be interpreted as EAK certification claims.

## Attribution and reuse

The repository-level `LICENSE` remains the governing Apache-2.0 license unless a file or third-party dependency states otherwise. When code is extracted or adapted from the upstream implementation, Git history and this provenance document preserve the source lineage.

Third-party models, datasets, services, APIs and assets can have their own licenses or usage terms. Their inclusion in an upstream or Quarry workflow does not automatically certify them for an EAK production deployment. Provider certification and deployment eligibility are separate EAK concerns.

## Separation rule

```text
Upstream / Quarry #001 implementation
        ↓ mining + evidence
Generic reusable capability/provider boundary
        ↓
EAK Kernel or Provider package

Medical semantics → eak/domains/medical/
Domain-agnostic semantics → eak/kernel/ or eak/providers/
```

A new domain must not require domain-specific conditionals in Kernel Core.
