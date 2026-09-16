from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .errors import ProviderDependencyError


class TavilyProvider:
    provider_id = "provider.tavily"
    capability = "web.search"

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def _client_or_default(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from tavily import TavilyClient
        except ImportError as exc:
            raise ProviderDependencyError("Install eak-providers[tavily]") from exc
        return TavilyClient()

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        response = self._client_or_default().search(query=query, max_results=max_results)
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "url": result.get("url"),
                "title": result.get("title"),
                "snippet": result.get("content"),
                "rawScore": result.get("score"),
                "retrievedAt": now,
                "provider": self.provider_id,
            }
            for result in response.get("results", [])
        ]
