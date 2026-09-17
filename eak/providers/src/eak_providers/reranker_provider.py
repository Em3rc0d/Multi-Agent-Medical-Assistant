from __future__ import annotations

from typing import Any, Iterable, Mapping

from .errors import ProviderDependencyError


class CrossEncoderRerankerProvider:
    """Generic reranker with explicit, unblended score semantics.

    Retrieval scores and cross-encoder scores are different measurements. This
    provider preserves them separately and never manufactures a universal
    confidence value by averaging incompatible score spaces.
    """

    provider_id = "provider.cross-encoder-reranker"
    capability = "knowledge.rerank"

    def __init__(
        self,
        model: Any | None = None,
        *,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self._model = model
        self.model_name = model_name

    def _model_or_default(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ProviderDependencyError("Install eak-providers[reranker]") from exc
        return CrossEncoder(self.model_name)

    def rerank(
        self,
        *,
        query: str,
        documents: Iterable[Mapping[str, Any]],
        text_field: str = "text",
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        docs = [dict(document) for document in documents]
        if not query.strip():
            raise ValueError("query is required")
        if limit is not None and limit < 1:
            raise ValueError("limit must be >= 1")
        if not docs:
            return []

        texts: list[str] = []
        for index, document in enumerate(docs):
            value = document.get(text_field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"document {index} is missing non-empty {text_field!r}")
            texts.append(value)

        raw_scores = self._model_or_default().predict([[query, text] for text in texts])
        scores = [float(score) for score in raw_scores]
        if len(scores) != len(docs):
            raise ValueError("reranker returned a score count that does not match documents")

        ranked: list[dict[str, Any]] = []
        for original_index, (document, score) in enumerate(zip(docs, scores, strict=True)):
            ranked.append({
                "document": document,
                "originalIndex": original_index,
                "rerankScore": score,
                "metric": "reranker.cross_encoder_raw_score",
                "provider": self.provider_id,
                "model": self.model_name,
            })
        ranked.sort(key=lambda item: (-item["rerankScore"], item["originalIndex"]))
        return ranked if limit is None else ranked[:limit]
