import asyncio

from app.backend.services.rag_retrieval import RagRetriever, RetrievalQuery


class FakeEmbeddings:
    configured = True

    async def embed(self, text: str) -> list[float]:
        assert text == "Which course covers machine organization?"
        return [0.1] * 1536


class FakeSupabase:
    async def rpc(self, function: str, parameters: dict):
        assert function == "retrieve_similar_documents"
        assert parameters["p_limit"] == 3
        assert parameters["p_department"] == "CS"
        assert len(parameters["p_query_embedding"]) == 1536
        return [{
            "id": "document-1",
            "source_type": "course",
            "source_id": "course-1",
            "document_text": "CS 361 covers machine organization.",
            "metadata": {"course_code": "CS 361", "department": "CS"},
            "similarity": 0.91,
            "embedding_model": "text-embedding-3-small",
            "embedding_version": "1",
        }]


async def _retrieve() -> list:
    retriever = RagRetriever(FakeSupabase(), FakeEmbeddings())
    return await retriever.retrieve(RetrievalQuery(
        question="Which course covers machine organization?", top_k=3, department_filter="CS"
    ))


def test_retrieve_calls_similar_documents_rpc() -> None:
    results = asyncio.run(_retrieve())
    assert results[0].document_id == "document-1"
    assert results[0].metadata["course_code"] == "CS 361"
