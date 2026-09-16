from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .compiler import GraphCompiler
from .graph import SemanticGraphValidator
from .model import CertificationRecord, Ref
from .policy import StaticPolicyAdapter
from .registry import CapabilityRegistry, CertificationRegistry, ProviderRegistry, SelectionMetadata
from .resolver import CapabilityResolver, ResolutionContext
from .schema import SchemaSet


class PaperConformanceHarness:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.schemas = SchemaSet(self.root / "schemas" / "v0.2")
        self.graph_validator = SemanticGraphValidator()
        self.capabilities, self.providers, self.certifications = self._load_registry()

    @staticmethod
    def load(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_registry(self) -> tuple[CapabilityRegistry, ProviderRegistry, CertificationRegistry]:
        registry_root = self.root / "conformance" / "fixtures" / "registry"
        capability_data = self.load(registry_root / "capabilities.json")["capabilities"]
        provider_data = self.load(registry_root / "providers.json")["providers"]
        selection_data = self.load(registry_root / "provider-selection.json")["selection"]
        certification_data = self.load(registry_root / "certifications.json")["certifications"]

        capabilities = CapabilityRegistry()
        for item in capability_data:
            self.schemas.validate(item)
            capabilities.add(item)

        selection_by_provider = {
            Ref.from_dict(item["provider"]): SelectionMetadata(
                policy_preference=item.get("policyPreference", 0),
                certification_specificity=item.get("certificationSpecificity", 0),
                quality_tier=item.get("qualityTier", 0),
                locality_preference=item.get("localityPreference", 0),
                cost_class=item.get("costClass", 0),
                ready=item.get("ready", True),
            ) for item in selection_data
        }
        providers = ProviderRegistry()
        for item in provider_data:
            self.schemas.validate(item)
            ref = Ref(item["metadata"]["id"], item["metadata"]["version"])
            providers.add_provider(item, selection_by_provider.get(ref, SelectionMetadata()))

        certifications = CertificationRegistry(
            CertificationRecord(
                provider=Ref.from_dict(item["provider"]),
                profile=item["profile"],
                status=item.get("status", "CERTIFIED"),
                domain=Ref.from_dict(item["domain"]) if item.get("domain") else None,
            ) for item in certification_data
        )
        return capabilities, providers, certifications

    def run_domain(self, domain: str) -> dict[str, Any]:
        fixture_root = self.root / "conformance" / "fixtures" / "paper"
        logical = self.load(fixture_root / f"{domain}.logical.execution-graph.json")
        expected = self.load(fixture_root / f"{domain}.physical.execution-graph.json")
        pack = self.load(fixture_root / f"{domain}.domain-pack.json")

        resolver = CapabilityResolver(self.providers, StaticPolicyAdapter(), self.certifications)
        compiler = GraphCompiler(self.schemas, self.graph_validator, resolver, self.capabilities)
        result = compiler.compile(
            logical,
            domain_pack=pack,
            context=ResolutionContext(domain=Ref(pack["metadata"]["id"], pack["metadata"]["version"])),
            execution_id=f"compile://{domain}",
        )
        expected_nodes = {node["id"]: node for node in expected["spec"]["nodes"]}
        return {
            "domain": domain,
            "pass": result.graph == expected,
            "compiled": result.graph,
            "expected": expected,
            "events": [event.type for event in result.events],
            "bindings": {node: ref.as_dict() for node, ref in result.provider_selections.items()},
            "expectedProviders": {node_id: node.get("provider") for node_id, node in expected_nodes.items() if node.get("provider")},
        }

    def run_all(self) -> list[dict[str, Any]]:
        return [self.run_domain(domain) for domain in ("medical", "aec", "legal")]
