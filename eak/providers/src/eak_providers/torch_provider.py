from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class TorchCallableProvider:
    """Generic inference seam for already-loaded PyTorch-style callables.

    Model acquisition, integrity hashes, preprocessing and certification are
    separate provider metadata; this wrapper intentionally does not download
    weights or perform network I/O during construction.
    """

    provider_id: str
    callable: Callable[[Any], Any]
    model_digest: str

    def infer(self, value: Any) -> dict[str, Any]:
        return {
            "result": self.callable(value),
            "provider": self.provider_id,
            "modelDigest": self.model_digest,
        }
