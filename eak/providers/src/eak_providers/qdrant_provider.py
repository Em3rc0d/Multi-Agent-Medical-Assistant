from __future__ import annotations

from typing import Any, Iterable

from .errors import ProviderDependencyError


class QdrantProvider:
    provider_id = "provider.qdrant"
    capability = "knowledge.retrieve"

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise ProviderDependencyError("Install eak-providers[qdrant]") from exc
        return QdrantClient(":memory:")

    def search(
        self,
        *,
        collection: str,
        vector: list[float],
        limit: int = 5,
        query_filter: Any | None = None,
    ) -> list[dict[str, Any]]:
        client = self._client_or_default()
        # Support both modern query_points and older search clients behind a
        # tiny compatibility seam, keeping the EAK result shape stable.
        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=collection,
                query=vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
            points: Iterable[Any] = getattr(response, "points", response)
        else:
            points = client.search(
                collection_name=collection,
                query_vector=vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
        return [
            {
                "id": str(getattr(point, "id", "")),
                "score": float(getattr(point, "score", 0.0)),
                "payload": dict(getattr(point, "payload", {}) or {}),
                "metric": "retrieval.provider_score",
                "provider": self.provider_id,
            }
            for point in points
        ]
