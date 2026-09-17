# EAK Standards Governance

EAK treats standards coverage as a **machine-verifiable evidence system**, not as a documentation checklist.

The registry in `standards-registry.json` is the canonical catalogue for horizontal platform, trust, supply-chain, interoperability and domain standards. Kernel code may consume the registry, but standard-specific business semantics remain outside Kernel Core.

## Claim semantics

Internal automation can establish only these states:

- **target** — adopted as a design target; required evidence is not yet complete.
- **partial** — some mapped controls/capabilities exist, but the evidence set is incomplete.
- **implemented** — the EAK implementation contains a concrete mechanism for the mapped scope.
- **verified** — automated or human-controlled EAK evidence verifies the mapped implementation scope.
- **external-attestation** — reserved for evidence issued by an authorized external assessor or standards body.

`implemented` and `verified` are **not** synonyms for ISO certification, regulatory approval, legal compliance, or clinical validation.

## Evidence-first model

Each standard declares evidence families such as `risk_register`, `sbom`, `provenance_export`, `conformance_test`, `privacy_assessment`, `restore_evidence`, or domain-specific validation. A deployment profile passes only when every required evidence family for the selected standards profiles is present and non-empty.

```text
Standard / Framework
        ↓
Standards Registry
        ↓
Profile selection
        ↓
Required evidence families
        ↓
EvidenceGraph / artifacts / CI / human review
        ↓
StandardsGate
        ↓
PASS for internal scope
or
FAIL-CLOSED
```

## Coverage layers

### Platform baseline

AI governance and risk, information security, privacy, cybersecurity, secure development, software quality and GenAI security are mapped through ISO/IEC 42001, ISO/IEC 23894, ISO/IEC 27001, ISO/IEC 27701, ISO/IEC 25010, NIST AI RMF, NIST CSF, NIST SSDF and OWASP LLM Top 10.

### Trust and software supply chain

W3C PROV-O, OpenTelemetry, SLSA, CycloneDX and SPDX define provenance, telemetry and software supply-chain evidence targets.

### Agent interoperability

MCP `2026-07-28` and A2A `1.0.0` are explicit interoperability targets. They belong in adapters/providers; neither protocol becomes the EAK internal contract model.

### Domain interoperability

- Medical: HL7 FHIR R5 and DICOM 2026c.
- AEC: IFC 4.3.2.0, IDS 1.0 and BCF 3.0.
- Legal: OASIS LegalDocML / Akoma Ntoso 1.0.

Jurisdiction-specific laws and regulations are intentionally separate from global technical standards. A Domain Pack may add them as policies/evidence profiles without changing the kernel.

## Governance rules

1. Every registry entry must use an official HTTPS source and an explicit version.
2. Drafts remain on the `watchlist`; they cannot silently replace a published baseline.
3. Version changes require an explicit registry diff, migration note and affected-evidence review.
4. A profile cannot reference an unknown standard.
5. Missing evidence fails closed.
6. Paid/copyrighted standards are mapped only at the public metadata and architectural level unless the project has licensed access; EAK does not reproduce proprietary control text.
7. Regulatory, clinical and jurisdictional compliance claims always require their own authorized evidence and review path.

## Profiles

`platform.baseline` is the horizontal platform profile. `interop.agents`, `domain.medical`, `domain.aec` and `domain.legal` are additive. A medical deployment, for example, should evaluate at least:

```text
platform.baseline
+ interop.agents      # when external agent/tool interoperability is enabled
+ domain.medical
+ jurisdiction profile(s)
+ deployment profile
```

The standards layer therefore stays composable instead of producing a single misleading global "compliant" boolean.
