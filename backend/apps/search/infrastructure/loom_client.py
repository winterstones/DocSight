"""
SEMAINE 1 — Implémentation concrète de AbstractSearchEngine via l'API REST de Loom.

Loom expose une API REST documentée sur https://api.loom/docs
Ce client traduit nos appels abstraits en requêtes HTTP vers Loom.
"""
import httpx
from django.conf import settings

from apps.search.domain.interfaces import (
    AbstractSearchEngine,
    ChatResponse,
    ChatMessage,
    SearchResponse,
    SearchResult,
    UploadResult,
)


class LoomSearchEngine(AbstractSearchEngine):
    """
    Consomme l'API REST de Loom.
    Injecté en production via la factory.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.LOOM_API_URL
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

    async def search(
        self,
        query: str,
        tags: list[str] | None = None,
        file_types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        params = {
            "query": query,
            "page": page,
            "page_size": page_size,
        }
        if tags:
            params["tags"] = ",".join(tags)
        if file_types:
            params["file_types"] = ",".join(file_types)

        response = await self._client.get("/api/search/", params=params)
        response.raise_for_status()
        data = response.json()

        return SearchResponse(
            results=[self._parse_result(r) for r in data.get("results", [])],
            total=data.get("total", 0),
            query=query,
            page=page,
            page_size=page_size,
        )

    async def upload(
        self,
        file_bytes: bytes,
        filename: str,
        tags: list[str] | None = None,
    ) -> UploadResult:
        files = {"file": (filename, file_bytes)}
        data  = {"tags": ",".join(tags)} if tags else {}

        response = await self._client.post("/api/upload/", files=files, data=data)
        response.raise_for_status()
        result = response.json()

        return UploadResult(
            document_id=result["id"],
            filename=filename,
            status=result.get("status", "processing"),
        )

    async def chat(
        self,
        question: str,
        document_ids: list[str] | None = None,
    ) -> ChatResponse:
        payload = {"question": question}
        if document_ids:
            payload["document_ids"] = document_ids

        response = await self._client.post("/api/chat/", json=payload)
        response.raise_for_status()
        data = response.json()

        return ChatResponse(
            answer=data["answer"],
            sources=[self._parse_result(s) for s in data.get("sources", [])],
        )

    async def get_tags(self) -> list[str]:
        response = await self._client.get("/api/tags/")
        response.raise_for_status()
        return response.json().get("tags", [])

    def _parse_result(self, raw: dict) -> SearchResult:
        return SearchResult(
            id=raw["id"],
            title=raw.get("title", raw.get("filename", "Sans titre")),
            content_preview=raw.get("content_preview", ""),
            file_type=raw.get("file_type", "unknown"),
            tags=raw.get("tags", []),
            score=raw.get("score", 0.0),
            thumbnail_url=raw.get("thumbnail_url"),
        )

    async def aclose(self) -> None:
        await self._client.aclose()
