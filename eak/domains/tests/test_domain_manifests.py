import json
from pathlib import Path

from eak_kernel.schema import SchemaSet

ROOT = Path(__file__).parents[2]


def test_all_domain_pack_manifests_validate_against_kernel_contract():
    schemas = SchemaSet(ROOT / "kernel" / "schemas" / "v0.2")
    packs = sorted((ROOT / "domains").glob("*/domain-pack.json"))
    assert {path.parent.name for path in packs} == {"medical", "aec", "legal"}
    for path in packs:
        schemas.validate(json.loads(path.read_text(encoding="utf-8")))
