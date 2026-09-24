"""Query-time RAG retrieval: embed user query, search, filter, rank."""

import logging
from typing import Any

from pydantic import BaseModel, Field

from app.backend.services.embeddings import EmbeddingClient
from app.backend.services.supabase import SupabaseClient


logger = logging.getLogger(__name__)


class RetrievalResult(BaseModel):
    """A single retrieved document with its relevance score."""

    document_id: str
    source_type: str
    source_id: str
    document_text: str
    metadata: dict[str, Any]
    similarity_score: float = Field(ge=0, le=1)
    embedding_model: str
    embedding_version: str


class RetrievalQuery(BaseModel):
    """A query for RAG retrieval."""

    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    department_filter: str | None = None
    course_level_filter: int | None = Field(default=None, ge=100, le=599)


class RagRetriever:
    """Retrieve relevant academic documents via semantic search."""

    def __init__(
        self,
        supabase_client: SupabaseClient | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.supabase = supabase_client or SupabaseClient()
        self.embeddings = embedding_client or EmbeddingClient()

    async def retrieve(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """
        Retrieve relevant documents for a user question.

        Args:
            query: The retrieval query with question and optional filters

        Returns:
            List of retrieved documents ranked by relevance

        Raises:
            ValueError: If embedding generation fails or query is invalid
        """
        if not self.embeddings.configured:
            logger.warning(
                "Embedding API not configured; returning empty results. "
                "Set OPENROUTER_API_KEY to enable RAG retrieval."
            )
            return []

        # Generate embedding for the user question
        try:
            query_embedding = await self.embeddings.embed(query.question)
            logger.info(f"Generated query embedding for: {query.question[:50]}...")
        except Exception as exc:
            logger.error(f"Failed to embed query: {exc}")
            raise

        rows = await self.supabase.rpc(
            "retrieve_similar_documents",
            {
                "p_query_embedding": query_embedding,
                "p_limit": query.top_k,
                "p_department": query.department_filter,
                "p_course_level": query.course_level_filter,
            },
        )
        return [RetrievalResult(
            document_id=str(row["id"]),
            source_type=row["source_type"],
            source_id=str(row["source_id"]),
            document_text=row["document_text"],
            metadata=row.get("metadata") or {},
            similarity_score=float(row["similarity"]),
            embedding_model=row["embedding_model"],
            embedding_version=row["embedding_version"],
        ) for row in rows]

    async def retrieve_similar_raw(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Low-level retrieval by embedding vector.

        (Intended for testing and advanced use cases)
        """
        if not query_embedding or len(query_embedding) != 1536:
            raise ValueError(f"Query embedding must have dimension 1536")

        if not 1 <= top_k <= 20:
            raise ValueError("top_k must be between 1 and 20")
        logger.info(f"Searching for {top_k} similar documents...")
        return await self.supabase.rpc(
            "retrieve_similar_documents",
            {"p_query_embedding": query_embedding, "p_limit": top_k},
        )
