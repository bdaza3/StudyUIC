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
    course_level_filter: int | None = None


class RagRetriever:
    """Retrieve relevant academic documents via semantic search."""

    def __init__(
        self,
        supabase_client: SupabaseClient | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.supabase = supabase_client
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

        # Call Supabase RPC to retrieve similar documents
        # (This requires the backend to have direct Supabase access, which we'll
        # configure via SQL function rather than REST API for this operation)
        #
        # For now, return a placeholder indicating the retrieval would happen
        # The actual retrieval would call retrieve_similar_documents RPC
        logger.info(
            f"Would retrieve {query.top_k} documents with embedding "
            f"(department={query.department_filter}, level={query.course_level_filter})"
        )

        # This is a stub for now; the full implementation requires:
        # 1. Direct pgvector query via Supabase RPC
        # 2. Proper error handling for missing/malformed embeddings
        # 3. Ranking and score normalization
        return []

    async def retrieve_similar_raw(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Low-level retrieval by embedding vector.

        (Intended for testing and advanced use cases)
        """
        if not query_embedding or len(query_embedding) != 1536:
            raise ValueError(f"Query embedding must have dimension 1536")

        logger.info(f"Searching for {top_k} similar documents...")
        # Would call Supabase RPC here
        return []
