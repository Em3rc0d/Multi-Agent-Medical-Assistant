import json
from pathlib import Path

from jsonschema import Draft202012Validator

from eak_kernel.schema import SchemaSet

ROOT = Path(__file__).parents[1]
EXPECTED = {
    "common.schema.json",
    "capability.schema.json",
    "provider.schema.json",
    "artifact.schema.json",
    "domain-pack.schema.json",
    "execution-context.schema.json",
    "execution-graph.schema.json",
    "evidence-graph.schema.json",
    "policy.schema.json",
    "evaluation-certification.schema.json",
}


def test_all_v02_schema_documents_exist_and_are_meta_valid():
    schema_dir = ROOT / "schemas" / "v0.2"
    actual = {path.name for path in schema_dir.glob("*.schema.json")}
    assert actual == EXPECTED
    for path in sorted(schema_dir.glob("*.schema.json")):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_paper_fixtures_are_contract_valid():
    schemas = SchemaSet(ROOT / "schemas" / "v0.2")
    for path in sorted((ROOT / "conformance" / "fixtures" / "paper").glob("*.json")):
        schemas.validate(json.loads(path.read_text(encoding="utf-8")))
