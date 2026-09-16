from types import SimpleNamespace

from eak_providers.qdrant_provider import QdrantProvider
from eak_providers.reranker_provider import CrossEncoderRerankerProvider
from eak_providers.tavily_provider import TavilyProvider
from eak_providers.torch_provider import TorchCallableProvider


class FakeQdrant:
    def query_points(self, **kwargs):
        return SimpleNamespace(points=[SimpleNamespace(id=7, score=0.81, payload={"source": "doc"})])


class FakeTavily:
    def search(self, **kwargs):
        return {"results": [{"url": "https://example.test", "title": "Result", "content": "Evidence", "score": 0.7}]}


class FakeCrossEncoder:
    def predict(self, pairs):
        assert pairs == [["query", "alpha"], ["query", "beta"]]
        return [0.25, 2.5]


def test_qdrant_preserves_structured_scores_and_payload():
    result = QdrantProvider(FakeQdrant()).search(collection="x", vector=[0.1, 0.2])
    assert result[0]["score"] == 0.81
    assert result[0]["metric"] == "retrieval.provider_score"
    assert result[0]["payload"]["source"] == "doc"


def test_reranker_keeps_raw_score_separate_from_retrieval_score():
    documents = [
        {"id": "a", "text": "alpha", "retrievalScore": 0.99},
        {"id": "b", "text": "beta", "retrievalScore": 0.51},
    ]
    result = CrossEncoderRerankerProvider(FakeCrossEncoder(), model_name="fake/v1").rerank(
        query="query", documents=documents
    )
    assert [item["document"]["id"] for item in result] == ["b", "a"]
    assert result[0]["rerankScore"] == 2.5
    assert result[0]["document"]["retrievalScore"] == 0.51
    assert result[0]["metric"] == "reranker.cross_encoder_raw_score"
    assert "confidence" not in result[0]


def test_reranker_is_stable_for_equal_scores_and_supports_limit():
    class EqualScores:
        def predict(self, pairs):
            return [1.0 for _ in pairs]

    result = CrossEncoderRerankerProvider(EqualScores()).rerank(
        query="query",
        documents=[{"text": "first"}, {"text": "second"}],
        limit=1,
    )
    assert result[0]["originalIndex"] == 0


def test_tavily_preserves_structured_provenance_fields():
    result = TavilyProvider(FakeTavily()).search("query")
    assert result[0]["url"] == "https://example.test"
    assert result[0]["rawScore"] == 0.7
    assert result[0]["retrievedAt"].endswith("+00:00")


def test_torch_provider_never_downloads_model_weights():
    provider = TorchCallableProvider(
        provider_id="provider.test.model",
        callable=lambda value: value * 2,
        model_digest="sha256:" + "a" * 64,
    )
    result = provider.infer(3)
    assert result["result"] == 6
    assert result["modelDigest"].startswith("sha256:")
