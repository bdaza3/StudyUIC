import os
from typing import Any

import httpx


class SupabaseClient:
    """Minimal Supabase PostgreSQL REST client for backend operations."""

    def __init__(
        self, url: str | None = None, api_key: str | None = None, timeout: float = 30
    ) -> None:
        self.url = url or os.getenv("SUPABASE_URL", "")
        self.api_key = api_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout = timeout

        if not self.url or not self.api_key:
            raise ValueError(
                "Supabase URL and SERVICE_ROLE_KEY required. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY environment variables."
            )

    async def query(self, table: str, select: str = "*", **filters) -> list[dict[str, Any]]:
        """
        Execute a SELECT query via Supabase REST API.

        Args:
            table: Table name
            select: Columns to select
            **filters: Equality filters (k=v becomes "k=eq.v")

        Returns:
            List of rows matching the query
        """
        url = f"{self.url}/rest/v1/{table}?select={select}"
        for key, value in filters.items():
            url += f"&{key}=eq.{value}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    async def fetch_courses(self) -> list[dict[str, Any]]:
        """Fetch all active courses with academic metadata."""
        return await self.query(
            "courses",
            select="id,course_code,title,department,credits,course_level,description,prerequisites,corequisites,long_description",
            active="true",
        )

    async def insert_rag_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """
        Insert RAG documents.

        Returns:
            List of inserted document IDs
        """
        url = f"{self.url}/rest/v1/rag_documents"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Prefer": "return=representation",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=documents)

        response.raise_for_status()
        result = response.json()

        if isinstance(result, list):
            return [doc["id"] for doc in result]
        return []

    async def upsert_rag_document(self, document: dict[str, Any]) -> str:
        """
        Upsert (insert or update) a single RAG document by content_hash.

        Returns:
            The document ID
        """
        url = f"{self.url}/rest/v1/rag_documents"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Prefer": "return=representation",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                json=document,
            )

        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and result:
            return result[0]["id"]
        return ""
