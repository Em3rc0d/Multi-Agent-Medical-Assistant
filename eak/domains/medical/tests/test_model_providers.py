from eak_domain_medical import ChestXRayResearchProvider, SkinLesionResearchProvider

DIGEST = "sha256:" + "a" * 64


def test_xray_wrapper_is_review_required_and_non_diagnostic():
    provider = ChestXRayResearchProvider(predictor=lambda _: "normal", model_digest=DIGEST)
    result = provider.analyze("image.png").as_dict()
    assert result["result"]["classification"] == "normal"
    assert result["requiresHumanReview"] is True
    assert result["intendedUse"] == "research_and_professional_decision_support"
    assert "diagnosis" not in result


def test_skin_wrapper_does_not_download_and_returns_artifact_reference():
    calls = []
    provider = SkinLesionResearchProvider(
        segmenter=lambda source, target: calls.append((source, target)) or "artifact://mask/1",
        model_digest=DIGEST,
    )
    result = provider.analyze("skin.jpg", "mask.png").as_dict()
    assert calls == [("skin.jpg", "mask.png")]
    assert result["result"]["segmentationArtifact"] == "artifact://mask/1"
    assert result["requiresHumanReview"] is True
