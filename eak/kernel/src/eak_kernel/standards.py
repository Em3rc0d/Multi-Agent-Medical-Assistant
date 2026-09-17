from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


ALLOWED_COVERAGE = {"target", "partial", "implemented", "verified", "external-attestation"}
ALLOWED_STATUS = {"published", "recommendation", "framework", "watch"}


@dataclass(frozen=True)
class StandardSpec:
    id: str
    title: str
    authority: str
    version: str
    category: str
    status: str
    coverage: str
    source: str
    required_evidence: tuple[str, ...]


@dataclass(frozen=True)
class StandardsGateResult:
    passed: bool
    missing_evidence: tuple[str, ...]
    unknown_standards: tuple[str, ...]
    notes: tuple[str, ...] = ()


class StandardsRegistry:
    """Machine-readable standards catalogue and profile resolver.

    This class deliberately distinguishes architectural alignment from external
    certification. Registry entries record targets and evidence expectations;
    they never turn an internal test result into a regulatory or ISO claim.
    """

    def __init__(self, document: Mapping[str, Any]) -> None:
        self.document = dict(document)
        self.schema_version = str(self.document.get("schemaVersion", ""))
        self._standards: dict[str, StandardSpec] = {}
        self._profiles: dict[str, tuple[str, ...]] = {}
        self._load()

    @classmethod
    def from_file(cls, path: str | Path) -> "StandardsRegistry":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _load(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("Unsupported standards registry schemaVersion")

        standards = self.document.get("standards")
        profiles = self.document.get("profiles")
        if not isinstance(standards, list) or not isinstance(profiles, dict):
            raise ValueError("Registry requires standards[] and profiles{}")

        for raw in standards:
            if not isinstance(raw, dict):
                raise ValueError("Standard entries must be objects")
            spec = StandardSpec(
                id=str(raw["id"]),
                title=str(raw["title"]),
                authority=str(raw["authority"]),
                version=str(raw["version"]),
                category=str(raw["category"]),
                status=str(raw["status"]),
                coverage=str(raw["coverage"]),
                source=str(raw["source"]),
                required_evidence=tuple(str(value) for value in raw.get("requiredEvidence", ())),
            )
            if spec.id in self._standards:
                raise ValueError(f"Duplicate standard id: {spec.id}")
            if spec.status not in ALLOWED_STATUS:
                raise ValueError(f"Unsupported status for {spec.id}: {spec.status}")
            if spec.coverage not in ALLOWED_COVERAGE:
                raise ValueError(f"Unsupported coverage for {spec.id}: {spec.coverage}")
            if not spec.source.startswith("https://"):
                raise ValueError(f"Official source must use https for {spec.id}")
            if not spec.required_evidence:
                raise ValueError(f"Standard requires at least one evidence family: {spec.id}")
            self._standards[spec.id] = spec

        for profile_id, members in profiles.items():
            if not isinstance(members, list) or not members:
                raise ValueError(f"Profile must contain standards: {profile_id}")
            refs = tuple(str(member) for member in members)
            unknown = sorted(ref for ref in refs if ref not in self._standards)
            if unknown:
                raise ValueError(f"Profile {profile_id} references unknown standards: {unknown}")
            self._profiles[str(profile_id)] = refs

    def standard(self, standard_id: str) -> StandardSpec:
        return self._standards[standard_id]

    def profile(self, profile_id: str) -> tuple[StandardSpec, ...]:
        try:
            refs = self._profiles[profile_id]
        except KeyError as exc:
            raise KeyError(f"Unknown standards profile: {profile_id}") from exc
        return tuple(self._standards[ref] for ref in refs)

    def profile_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._profiles))

    def all(self) -> tuple[StandardSpec, ...]:
        return tuple(self._standards[key] for key in sorted(self._standards))


class StandardsGate:
    """Fail-closed evidence gate for one or more standards profiles."""

    def __init__(self, registry: StandardsRegistry) -> None:
        self.registry = registry

    def evaluate(
        self,
        *,
        profiles: Iterable[str],
        evidence: Mapping[str, Any],
    ) -> StandardsGateResult:
        required: set[str] = set()
        unknown_standards: set[str] = set()
        notes: list[str] = []

        for profile_id in profiles:
            for spec in self.registry.profile(profile_id):
                required.update(spec.required_evidence)
                if spec.coverage in {"target", "partial"}:
                    notes.append(f"{spec.id}:{spec.coverage}")

        supplied = {
            str(key)
            for key, value in evidence.items()
            if value not in (None, False, "", (), [], {})
        }
        missing = tuple(sorted(required - supplied))
        return StandardsGateResult(
            passed=not missing and not unknown_standards,
            missing_evidence=missing,
            unknown_standards=tuple(sorted(unknown_standards)),
            notes=tuple(sorted(set(notes))),
        )
