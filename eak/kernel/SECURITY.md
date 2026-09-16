# EAK Security Policy

EAK is an engineering-incubation kernel for verifiable expert systems. It is not, by itself, a medical device, legal authority, structural-analysis product, or autonomous decision maker.

## Security invariants

- Fail closed on missing certification, provider readiness, policy decisions, or schema compatibility.
- Treat user input, retrieved content, domain packs, providers, models, remote agents, and human approvals as separate trust boundaries.
- Never store provider credentials in `ExecutionContext` or domain manifests; store only credential references.
- Artifact access is tenant-scoped and policy-gated. Content capture in traces is disabled by default.
- Side-effecting providers must declare effects and idempotency semantics before execution.
- High-risk workflows may require authenticated human approval before execution continues.
- Runtime adapters must not leak runtime-native state into EAK contracts.

## Reporting

Do not open a public issue for suspected vulnerabilities containing secrets, personal data, or exploit details. Use the repository owner's private security-reporting channel when enabled. Until then, contact the maintainer privately through the GitHub account associated with this repository.
