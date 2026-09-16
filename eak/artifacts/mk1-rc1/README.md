# EAK MK1 RC1 delta

This directory carries the reproducible delta from the frozen MK1 contract-first snapshot to RC1.

## Base snapshot

`eak/artifacts/mk1-contract-first/`

Expected reconstructed base archive SHA-256:

`5449e3b2dc0cf912892e635970d809a80238c88a5c8c8389bb02e3afeb1cd636`

## RC1 patch

Concatenate in lexical order:

```bash
cat eak-mk1-rc1.patch.part* > eak-mk1-rc1.patch
```

Expected patch SHA-256:

`159cfd7fe8b1d7880a930ad0dfc22b7aef945e1782f03145c19ed5d02524a99c`

Apply from the root of the reconstructed base snapshot:

```bash
patch -p1 < eak-mk1-rc1.patch
```

RC1 adds the artifact boundary, evidence/PROV projection, approval identity checks, evaluation/certification primitives, DomainPack loading, observability boundary, package metadata updates, and real LangGraph integration tests. GitHub Actions is the authoritative package-level runtime gate because it can install the optional LangGraph dependency.
