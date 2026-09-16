"""Optional EAK provider implementations.

Providers live outside Kernel Core. Heavy dependencies are imported lazily so
installing the kernel does not pull domain- or tool-specific runtimes.
"""

from .docling_provider import DoclingProvider
from .qdrant_provider import QdrantProvider
from .tavily_provider import TavilyProvider
from .torch_provider import TorchCallableProvider

__all__ = ["DoclingProvider", "QdrantProvider", "TavilyProvider", "TorchCallableProvider"]
