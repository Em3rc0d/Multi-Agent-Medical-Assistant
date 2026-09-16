"""EAK contract-first kernel package."""

from .compiler import CompileResult, GraphCompiler
from .conformance import PaperConformanceHarness
from .crypto import AESGCMCipher, EncryptedArtifactStore
from .graph import SemanticGraphValidator
from .readiness import DeploymentEvidence, ProductionReadinessGate, ReadinessResult
from .recovery import SnapshotManifest, build_manifest, verify_manifest
from .resolver import CapabilityResolver
from .schema import SchemaSet
from .secrets import CompositeSecretProvider, EnvironmentSecretProvider, SecretValue
from .security import Principal, RBACAuthorizer, RoleGrant
from .workqueue import SQLiteWorkQueue, WorkItem

__all__ = [
    "AESGCMCipher",
    "CapabilityResolver",
    "CompileResult",
    "CompositeSecretProvider",
    "DeploymentEvidence",
    "EncryptedArtifactStore",
    "EnvironmentSecretProvider",
    "GraphCompiler",
    "PaperConformanceHarness",
    "Principal",
    "ProductionReadinessGate",
    "RBACAuthorizer",
    "ReadinessResult",
    "RoleGrant",
    "SQLiteWorkQueue",
    "SchemaSet",
    "SecretValue",
    "SemanticGraphValidator",
    "SnapshotManifest",
    "WorkItem",
    "build_manifest",
    "verify_manifest",
]
