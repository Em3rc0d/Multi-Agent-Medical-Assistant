from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class MedicalModelResult:
    capability: str
    provider: str
    model_digest: str
    result: Any
    intended_use: str = "research_and_professional_decision_support"
    requires_human_review: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "provider": self.provider,
            "modelDigest": self.model_digest,
            "result": self.result,
            "intendedUse": self.intended_use,
            "requiresHumanReview": self.requires_human_review,
        }


class ChestXRayResearchProvider:
    """Quarry-derived X-ray inference boundary.

    The injected predictor is intentionally separate from model acquisition and
    certification. This wrapper never calls the network or downloads weights.
    """

    capability = "medical.imaging.chest_xray.classify"

    def __init__(self, *, predictor: Callable[[str], Any], model_digest: str, provider_id: str = "medical.xray.quarry") -> None:
        if not model_digest.startswith("sha256:"):
            raise ValueError("model_digest must be a sha256 content digest")
        self.predictor = predictor
        self.model_digest = model_digest
        self.provider_id = provider_id

    def analyze(self, image_path: str) -> MedicalModelResult:
        return MedicalModelResult(
            capability=self.capability,
            provider=self.provider_id,
            model_digest=self.model_digest,
            result={"classification": self.predictor(image_path)},
        )


class SkinLesionResearchProvider:
    """Segmentation boundary replacing Quarry #001's import-time download path."""

    capability = "medical.dermatology.lesion.segment"

    def __init__(self, *, segmenter: Callable[[str, str], Any], model_digest: str, provider_id: str = "medical.skin.quarry") -> None:
        if not model_digest.startswith("sha256:"):
            raise ValueError("model_digest must be a sha256 content digest")
        self.segmenter = segmenter
        self.model_digest = model_digest
        self.provider_id = provider_id

    def analyze(self, image_path: str, output_path: str) -> MedicalModelResult:
        return MedicalModelResult(
            capability=self.capability,
            provider=self.provider_id,
            model_digest=self.model_digest,
            result={"segmentationArtifact": self.segmenter(image_path, output_path)},
        )
