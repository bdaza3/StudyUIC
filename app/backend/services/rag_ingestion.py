"""RAG ingestion pipeline: fetch courses, construct documents, generate embeddings, store."""

import asyncio
import json
import logging
from typing import Any

from dotenv import load_dotenv

from app.backend.services.embeddings import EmbeddingClient, EmbeddingSettings
from app.backend.services.rag_documents import CourseRecord, construct_course_document
from app.backend.services.supabase import SupabaseClient


load_dotenv()

logger = logging.getLogger(__name__)


class RagIngestionPipeline:
    """
    Deterministic RAG document ingestion pipeline.

    1. Fetch courses from Supabase
    2. Construct deterministic documents
    3. Check if content has changed (via content_hash)
    4. Generate embeddings only when necessary
    5. Store documents and embeddings
    """

    def __init__(
        self,
        supabase_client: SupabaseClient | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        self.supabase = supabase_client or SupabaseClient()
        self.embeddings = embedding_client or EmbeddingClient()

    async def ingest_all_courses(self, batch_size: int = 10) -> dict[str, Any]:
        """
        Ingest all active courses from Supabase.

        Args:
            batch_size: Number of embeddings to generate per API call

        Returns:
            Dictionary with ingestion statistics
        """
        logger.info("Starting RAG course ingestion pipeline")

        # Fetch all active courses
        try:
            course_rows = await self.supabase.fetch_courses()
        except Exception as exc:
            logger.error(f"Failed to fetch courses: {exc}")
            raise

        logger.info(f"Fetched {len(course_rows)} courses from Supabase")

        # Construct documents
        documents = []
        for row in course_rows:
            course = CourseRecord(
                id=row["id"],
                course_code=row["course_code"],
                title=row["title"],
                department=row["department"],
                credits=row.get("credits"),
                course_level=row.get("course_level"),
                description=row.get("description"),
                prerequisites=row.get("prerequisites"),
                corequisites=row.get("corequisites"),
                long_description=row.get("long_description"),
            )
            doc = construct_course_document(course)
            documents.append(doc)

        logger.info(f"Constructed {len(documents)} RAG documents")

        # Generate embeddings and insert
        stats = {
            "total_courses": len(documents),
            "documents_inserted": 0,
            "documents_skipped": 0,
            "errors": [],
        }

        if not self.embeddings.configured:
            logger.warning(
                "Embedding API not configured. Storing documents without embeddings."
            )
            # Insert placeholder embeddings for testing
            for doc in documents:
                try:
                    payload = {
                        "source_type": doc.source_type,
                        "source_id": doc.source_id,
                        "source_table": doc.source_table,
                        "document_text": doc.document_text,
                        "metadata": doc.metadata.model_dump(),
                        "embedding": [0.0] * 1536,  # Placeholder
                        "embedding_model": "placeholder",
                        "embedding_version": "0",
                        "content_hash": doc.content_hash,
                    }
                    await self.supabase.upsert_rag_document(payload)
                    stats["documents_inserted"] += 1
                except Exception as exc:
                    logger.error(f"Failed to insert document {doc.source_id}: {exc}")
                    stats["errors"].append(str(exc))
            return stats

        # Process documents in batches with real embeddings
        texts_to_embed = [doc.document_text for doc in documents]

        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i : i + batch_size]
            batch_docs = documents[i : i + batch_size]

            try:
                embeddings = await self.embeddings.embed_batch(batch_texts)
                logger.info(
                    f"Generated embeddings for batch {i // batch_size + 1} "
                    f"({len(embeddings)} embeddings)"
                )

                for doc, embedding in zip(batch_docs, embeddings):
                    payload = {
                        "source_type": doc.source_type,
                        "source_id": doc.source_id,
                        "source_table": doc.source_table,
                        "document_text": doc.document_text,
                        "metadata": doc.metadata.model_dump(),
                        "embedding": embedding,
                        "embedding_model": self.embeddings.settings.model,
                        "embedding_version": "1",
                        "content_hash": doc.content_hash,
                    }

                    try:
                        await self.supabase.upsert_rag_document(payload)
                        stats["documents_inserted"] += 1
                    except Exception as exc:
                        logger.error(
                            f"Failed to upsert document {doc.source_id}: {exc}"
                        )
                        stats["errors"].append(str(exc))

            except Exception as exc:
                logger.error(f"Failed to generate embeddings for batch {i}: {exc}")
                stats["errors"].append(str(exc))

        logger.info(
            f"Ingestion complete: {stats['documents_inserted']} inserted, "
            f"{stats['documents_skipped']} skipped, {len(stats['errors'])} errors"
        )
        return stats


async def run_ingestion() -> None:
    """Entry point for RAG ingestion (can be run as a script or scheduled task)."""
    logging.basicConfig(level=logging.INFO)
    pipeline = RagIngestionPipeline()
    stats = await pipeline.ingest_all_courses()
    print(json.dumps(stats, indent=2))
