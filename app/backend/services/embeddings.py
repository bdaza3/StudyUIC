import json
import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class EmbeddingSettings:
    """Configuration for embedding generation."""

    api_key: str | None
    model: str
    base_url: str
    dimensions: int
    timeout_seconds: float

    @classmethod
    def from_environment(cls) -> "EmbeddingSettings":
        return cls(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1536")),
            timeout_seconds=float(os.getenv("EMBEDDING_TIMEOUT_SECONDS", "30")),
        )


class EmbeddingClient:
    """Client for generating embeddings via OpenRouter OpenAI-compatible API."""

    def __init__(self, settings: EmbeddingSettings | None = None) -> None:
        self.settings = settings or EmbeddingSettings.from_environment()

    @property
    def configured(self) -> bool:
        """Check if API credentials are available."""
        return bool(self.settings.api_key)

    async def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            A list of floats representing the embedding vector

        Raises:
            ValueError: If the embedding generation fails or API is not configured
        """
        if not self.configured:
            raise ValueError(
                "Embedding API not configured. Set OPENROUTER_API_KEY environment variable."
            )

        payload = {
            "model": self.settings.model,
            "input": text,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://studyuic.local",
            "X-Title": "StudyUIC RAG Embeddings",
        }

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.base_url.rstrip('/')}/embeddings",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        body: dict[str, Any] = response.json()

        try:
            embedding = body["data"][0]["embedding"]
            if not isinstance(embedding, list) or len(embedding) != self.settings.dimensions:
                raise ValueError(
                    f"Embedding has unexpected dimension {len(embedding)}; "
                    f"expected {self.settings.dimensions}"
                )
            return embedding
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenRouter returned an invalid embedding response") from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If embedding generation fails
        """
        if not self.configured:
            raise ValueError(
                "Embedding API not configured. Set OPENROUTER_API_KEY environment variable."
            )

        payload = {
            "model": self.settings.model,
            "input": texts,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://studyuic.local",
            "X-Title": "StudyUIC RAG Embeddings",
        }

        async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.base_url.rstrip('/')}/embeddings",
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        body: dict[str, Any] = response.json()

        try:
            embeddings = [item["embedding"] for item in body["data"]]
            for embedding in embeddings:
                if not isinstance(embedding, list) or len(embedding) != self.settings.dimensions:
                    raise ValueError(
                        f"Embedding has unexpected dimension {len(embedding)}; "
                        f"expected {self.settings.dimensions}"
                    )
            return embeddings
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("OpenRouter returned an invalid embedding response") from exc
