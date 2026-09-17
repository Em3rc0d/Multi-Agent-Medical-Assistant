# EAK Standards Intent

Standards governance is now an explicit engineering subsystem rather than scattered documentation.

Canonical artifacts live under `eak/governance/` and are enforced by `eak_kernel.standards.StandardsRegistry`, `StandardsGate`, JSON Schema validation and the dedicated `EAK Standards Governance` CI workflow.

The standards layer covers horizontal platform concerns plus Medical, AEC, Legal and agent interoperability profiles. It is evidence-first and fail-closed, and it deliberately distinguishes internal implementation/alignment evidence from external certification, regulatory approval, clinical validation or jurisdiction-specific legal compliance.
