from __future__ import annotations

from typing import Any

from .model import Ref
from .registry import ProviderRegistry


class ExecutionContextCompiler:
    def __init__(self, providers: ProviderRegistry):
        self.providers = providers

    def compile(
        self,
        *,
        execution_id: str,
        domain_pack: dict[str, Any],
        physical_graph: dict[str, Any],
        principal: dict[str, Any],
        tenant: str,
        policy_snapshot: Ref,
        inputs: list[str],
        trace_id: str,
        knowledge: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        capability_refs: list[dict[str, str]] = []
        resolved: list[dict[str, Any]] = []
        seen_capabilities: set[Ref] = set()
        for node in physical_graph["spec"]["nodes"]:
            if node["kind"] != "capability":
                continue
            capability = Ref.from_dict(node["capability"])
            provider = Ref.from_dict(node["provider"])
            if capability not in seen_capabilities:
                capability_refs.append(capability.as_dict())
                seen_capabilities.add(capability)
            provider_doc = self.providers.get(provider)
            digests = [value["digest"] for value in provider_doc["spec"].get("artifacts", [])]
            resolved.append(
                {
                    "capability": capability.as_dict(),
                    "provider": provider.as_dict(),
                    "artifactDigests": digests,
                }
            )

        return {
            "apiVersion": "eak/v0.2",
            "kind": "ExecutionContext",
            "metadata": {
                "id": execution_id.replace("execution://", ""),
                "version": "1.0.0",
                "displayName": "Compiled execution snapshot",
            },
            "spec": {
                "executionId": execution_id,
                "principal": principal,
                "tenant": tenant,
                "snapshots": {
                    "domain": {
                        "id": domain_pack["metadata"]["id"],
                        "version": domain_pack["metadata"]["version"],
                    },
                    "workflow": {
                        "id": physical_graph["metadata"]["id"].removesuffix(".compiled"),
                        "version": physical_graph["metadata"]["version"],
                    },
                    "capabilities": capability_refs,
                    "knowledge": knowledge or [
                        {"id": item["id"], "version": item["version"]}
                        for item in domain_pack["spec"]["registrations"].get("knowledge", [])
                    ],
                },
                "resolvedProviders": resolved,
                "inputs": inputs,
                "policySnapshot": policy_snapshot.as_dict(),
                "riskContext": {},
                "approvalRefs": [],
                "trace": {"traceId": trace_id, "contentCapture": "off"},
            },
        }
