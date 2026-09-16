from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ProviderDependencyError


class DoclingProvider:
    provider_id = "provider.docling"
    capability = "document.parse"

    def parse(self, path: str | Path) -> dict[str, Any]:
        """Parse a document without introducing medical semantics.

        Domain-specific image interpretation belongs to a Domain Pack/provider
        layered on top of this generic document capability.
        """
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise ProviderDependencyError("Install eak-providers[docling]") from exc

        source = Path(path)
        result = DocumentConverter().convert(str(source))
        document = result.document
        export_markdown = getattr(document, "export_to_markdown", None)
        text = export_markdown() if callable(export_markdown) else str(document)
        return {
            "source": str(source),
            "text": text,
            "document": document,
            "provider": self.provider_id,
        }
