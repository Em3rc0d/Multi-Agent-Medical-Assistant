# Quarry #001 → EAK Medical Extraction Map

| Quarry component | EAK destination | Decision |
| --- | --- | --- |
| `agents/agent_decision.py` | workflow/compiler/runtime concepts | rewrite; do not port named-agent routing |
| `agents/rag_agent/doc_parser.py` | `eak/providers` Docling provider | generalized |
| `vectorstore_qdrant.py` | Qdrant provider | generalized; preserve score semantics |
| `tavily_search.py` | Tavily provider | generalized; preserve structured provenance |
| Chest X-ray DenseNet | medical model provider | research-only until benchmark/certification gate passes |
| Skin lesion U-Net | medical model provider | rewritten boundary; legacy auto-download is not allowed |
| Brain tumor stub | none | excluded until implementation + evaluation exist |
| `LocalGuardrails` | Policy adapter / domain policy | replace; prompt is not policy authority |
| text `yes/no` validation | Approval contract | replace with authenticated identity + role verification |
| static `/data` and `/uploads` | ArtifactStore | replace; no direct static serving for restricted artifacts |

## Non-negotiable promotion gate

Wrapping a legacy model does **not** certify it. Promotion requires immutable model artifact digest, versioned preprocessing, representative evaluation data, explicit metrics/thresholds, human review policy and a CertificationRecord bound to that exact target tuple.
