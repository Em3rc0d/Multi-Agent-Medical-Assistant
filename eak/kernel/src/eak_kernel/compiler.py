from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .graph import SemanticGraphValidator
from .errors import ResolutionError
from .model import Event, Ref
from .resolver import CapabilityResolver, ResolutionContext
from .registry import CapabilityRegistry
from .schema import SchemaSet


@dataclass(frozen=True)
class CompileResult:
    graph: dict[str, Any]
    events: tuple[Event, ...]
    provider_selections: dict[str, Ref]


class GraphCompiler:
    def __init__(
        self,
        schemas: SchemaSet,
        graph_validator: SemanticGraphValidator,
        resolver: CapabilityResolver,
        capabilities: CapabilityRegistry,
    ):
        self.schemas = schemas
        self.graph_validator = graph_validator
        self.resolver = resolver
        self.capabilities = capabilities

    def compile(
        self,
        logical: dict[str, Any],
        *,
        domain_pack: dict[str, Any],
        context: ResolutionContext,
        execution_id: str = "compile://conformance",
    ) -> CompileResult:
        self.schemas.validate(logical)
        self.schemas.validate(domain_pack)
        self.graph_validator.validate(logical)
        if logical["spec"]["graphType"] != "logical":
            raise ValueError("Compiler input must be a logical graph")

        physical = SemanticGraphValidator.to_physical(logical)
        events: list[Event] = []
        selections: dict[str, Ref] = {}

        for node in physical["spec"]["nodes"]:
            if node["kind"] != "capability":
                continue
            capability = Ref.from_dict(node["capability"])
            try:
                self.capabilities.get(capability)
            except KeyError as exc:
                raise ResolutionError(
                    f"Capability contract is not registered: {capability.id}@{capability.version}"
                ) from exc
            selection = self.resolver.resolve(
                capability,
                domain_pack=domain_pack,
                context=context,
            )
            node["provider"] = selection.provider.as_dict()
            selections[node["id"]] = selection.provider
            events.append(
                Event(
                    type="ProviderResolved",
                    execution_id=execution_id,
                    payload={
                        "node": node["id"],
                        "capability": capability.as_dict(),
                        "provider": selection.provider.as_dict(),
                        "selectionProfile": selection.selection_profile,
                        "rejected": {
                            f"{ref.id}@{ref.version}": list(reasons)
                            for ref, reasons in selection.rejected.items()
                        },
                    },
                )
            )

        self.schemas.validate(physical)
        self.graph_validator.validate(physical)
        events.append(Event(type="GraphCompiled", execution_id=execution_id, payload={"graph": physical["metadata"]["id"]}))
        return CompileResult(physical, tuple(events), selections)
