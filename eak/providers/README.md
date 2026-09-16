# EAK Providers — MK2 Quarry Extraction

These adapters are the first controlled extraction from Quarry #001. They are intentionally outside Kernel Core.

## Rules

- Provider implementations expose deterministic, structured boundaries.
- Heavy dependencies are optional and lazily imported.
- No provider downloads model weights during import or construction.
- Search/retrieval results preserve structure and score semantics instead of flattening to strings.
- Egress, credentials, certification and artifact policy are decided by EAK before invocation.
- Domain interpretation belongs to Domain Packs, not generic providers.

## Initial providers

- `DoclingProvider`: generic document parsing.
- `QdrantProvider`: structured vector retrieval.
- `TavilyProvider`: structured web-search result normalization.
- `TorchCallableProvider`: model-inference seam with immutable model digest metadata.

These are incubation adapters, not production-certified providers.
