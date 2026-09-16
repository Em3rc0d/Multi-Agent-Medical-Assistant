from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .errors import SchemaValidationError


_KIND_TO_SCHEMA = {
    "Artifact": "artifact.schema.json",
    "Capability": "capability.schema.json",
    "DomainPack": "domain-pack.schema.json",
    "ExecutionContext": "execution-context.schema.json",
    "ExecutionGraph": "execution-graph.schema.json",
    "Policy": "policy.schema.json",
    "Provider": "provider.schema.json",
    "EvidenceGraph": "evidence-graph.schema.json",
    "EvaluationProfile": "evaluation-certification.schema.json",
    "EvaluationRun": "evaluation-certification.schema.json",
    "CertificationRecord": "evaluation-certification.schema.json",
}


class SchemaSet:
    def __init__(self, schema_dir: str | Path):
        self.schema_dir = Path(schema_dir)
        self.schemas: dict[str, dict[str, Any]] = {}
        resources: list[tuple[str, Resource[Any]]] = []
        for path in sorted(self.schema_dir.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.schemas[path.name] = schema
            schema_id = schema.get("$id")
            if schema_id:
                resources.append((schema_id, Resource.from_contents(schema)))
        self.registry = Registry().with_resources(resources)

    def validate(self, document: dict[str, Any]) -> None:
        kind = document.get("kind")
        schema_name = _KIND_TO_SCHEMA.get(str(kind))
        if not schema_name:
            raise SchemaValidationError(f"Unsupported or missing kind: {kind!r}")
        schema = self.schemas[schema_name]
        validator = Draft202012Validator(schema, registry=self.registry)
        errors = sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
        if errors:
            details = "; ".join(
                f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors[:8]
            )
            raise SchemaValidationError(f"{kind} failed schema validation: {details}")

    def validate_file(self, path: str | Path) -> dict[str, Any]:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        self.validate(document)
        return document
