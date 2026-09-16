# EAK MK1 Contract-First Snapshot

This directory preserves the complete clean MK1 incubation snapshot produced after freezing EAK Core Spec v0.2.

## Snapshot

- Source files: 80
- Test status before packaging: **20/20 passing**
- Archive format: `tar.xz`, Base64-split for GitHub connector transport
- Archive SHA-256: `5449e3b2dc0cf912892e635970d809a80238c88a5c8c8389bb02e3afeb1cd636`
- Branch: `eak/mk1-contract-first`

The snapshot contains the frozen specifications and schemas, Medical/AEC/Legal conformance fixtures, the contract-first kernel implementation, tests, and the LangGraph adapter contract/implementation work completed so far.

## Reassemble

From this directory:

```bash
cat eak-mk1-clean.tar.xz.b64.part* | base64 -d > eak-mk1-clean.tar.xz
sha256sum eak-mk1-clean.tar.xz
mkdir eak-mk1-clean
tar -xJf eak-mk1-clean.tar.xz -C eak-mk1-clean
```

Expected SHA-256:

```text
5449e3b2dc0cf912892e635970d809a80238c88a5c8c8389bb02e3afeb1cd636
```

## Engineering status

MK0 is frozen for engineering incubation. MK1 is active and contract-first. The generic conformance/compiler/runtime boundaries are green across Medical, AEC, and Legal paper fixtures. The LangGraph package-level integration gate against the selected supported API surface remains intentionally open, so Quarry #001 medical porting is still blocked.

`main` is intentionally unchanged by this snapshot until the incubation branch is reviewed and explicitly merged.
