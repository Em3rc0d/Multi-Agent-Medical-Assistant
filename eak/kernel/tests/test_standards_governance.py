import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from eak_kernel.standards import StandardsGate, StandardsRegistry


EAK_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = EAK_ROOT / "governance" / "standards-registry.json"
REGISTRY_SCHEMA = EAK_ROOT / "governance" / "standards-registry.schema.json"


def test_registry_conforms_to_its_json_schema():
    document = json.loads(REGISTRY.read_text(encoding="utf-8"))
    schema = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)


def test_standards_registry_is_machine_valid_and_profiles_resolve():
    registry = StandardsRegistry.from_file(REGISTRY)
    assert "platform.baseline" in registry.profile_ids()
    assert "domain.medical" in registry.profile_ids()
    assert registry.standard("mcp:2026-07-28").version == "2026-07-28"
    assert registry.standard("a2a:1.0.0").coverage == "target"
    assert len(registry.all()) >= 20


def test_all_registry_sources_are_official_https_and_versions_are_explicit():
    registry = StandardsRegistry.from_file(REGISTRY)
    for standard in registry.all():
        assert standard.source.startswith("https://")
        assert standard.version.strip()
        assert standard.required_evidence


def test_standards_gate_fails_closed_on_missing_evidence():
    registry = StandardsRegistry.from_file(REGISTRY)
    result = StandardsGate(registry).evaluate(
        profiles=("domain.legal",),
        evidence={"akn_schema_validation": "artifact://1"},
    )
    assert not result.passed
    assert "legal_document_provenance" in result.missing_evidence
    assert "jurisdiction_metadata" in result.missing_evidence
    assert "temporal_validity_test" in result.missing_evidence


def test_standards_gate_accepts_complete_profile_evidence_without_certification_claim():
    registry = StandardsRegistry.from_file(REGISTRY)
    profile = registry.profile("domain.aec")
    required = {
        evidence_name
        for standard in profile
        for evidence_name in standard.required_evidence
    }
    result = StandardsGate(registry).evaluate(
        profiles=("domain.aec",),
        evidence={name: f"evidence://{name}" for name in required},
    )
    assert result.passed
    assert result.missing_evidence == ()
    assert any(note.endswith(":target") for note in result.notes)


def test_unknown_profile_is_rejected():
    registry = StandardsRegistry.from_file(REGISTRY)
    with pytest.raises(KeyError):
        StandardsGate(registry).evaluate(profiles=("domain.unknown",), evidence={})


def test_registry_rejects_profile_referencing_unknown_standard():
    broken = {
        "schemaVersion": "1.0",
        "standards": [
            {
                "id": "example:1",
                "title": "Example",
                "authority": "Example",
                "version": "1",
                "category": "test",
                "status": "published",
                "coverage": "target",
                "source": "https://example.test/standard",
                "requiredEvidence": ["test_evidence"],
            }
        ],
        "profiles": {"broken": ["missing:1"]},
    }
    with pytest.raises(ValueError, match="unknown standards"):
        StandardsRegistry(broken)
