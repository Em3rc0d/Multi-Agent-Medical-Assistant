from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .model import CertificationRecord, Ref


class VersionedRegistry:
    def __init__(self) -> None:
        self._items: dict[Ref, dict[str, Any]] = {}

    def add(self, item: dict[str, Any]) -> Ref:
        ref = Ref(item["metadata"]["id"], item["metadata"]["version"])
        if ref in self._items:
            raise ValueError(f"Duplicate registry entry: {ref}")
        self._items[ref] = item
        return ref

    def get(self, ref: Ref) -> dict[str, Any]:
        return self._items[ref]

    def all(self) -> Iterable[tuple[Ref, dict[str, Any]]]:
        return tuple(self._items.items())


@dataclass(frozen=True)
class SelectionMetadata:
    policy_preference: int = 0
    certification_specificity: int = 0
    quality_tier: int = 0
    locality_preference: int = 0
    cost_class: int = 0
    ready: bool = True


@dataclass
class ProviderRegistry(VersionedRegistry):
    selection: dict[Ref, SelectionMetadata] = field(default_factory=dict)

    def __post_init__(self) -> None:
        VersionedRegistry.__init__(self)

    def add_provider(
        self, item: dict[str, Any], selection: SelectionMetadata | None = None
    ) -> Ref:
        ref = self.add(item)
        self.selection[ref] = selection or SelectionMetadata()
        return ref

    def implementing(self, capability: Ref) -> list[tuple[Ref, dict[str, Any], SelectionMetadata]]:
        result = []
        for ref, provider in self.all():
            implements = [Ref.from_dict(value) for value in provider["spec"]["implements"]]
            if capability in implements:
                result.append((ref, provider, self.selection[ref]))
        return result


class CapabilityRegistry(VersionedRegistry):
    pass


class CertificationRegistry:
    def __init__(self, records: Iterable[CertificationRecord] = ()) -> None:
        self.records = tuple(records)

    def certified(self, provider: Ref, profile: str, domain: Ref | None = None) -> bool:
        for record in self.records:
            if record.provider != provider or record.profile != profile or record.status != "CERTIFIED":
                continue
            if record.domain is None or domain is None or record.domain == domain:
                return True
        return False
