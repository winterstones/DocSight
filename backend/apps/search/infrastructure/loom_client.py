"""
SEMAINE 1 — Implémentation concrète de AbstractSearchEngine via l'API REST de Loom.

Loom expose une API REST documentée sur https://api.loom/docs
Ce client traduit nos appels abstraits en requêtes HTTP vers Loom.
"""
import httpx
from django.conf import settings
import boto3
from asgiref.sync import sync_to_async
from decouple import config

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
        # Fetch a valid Point In Time query_id from Loom API
        query_resp = await self._client.post("/v1/files/query")
        query_resp.raise_for_status()
        query_id = query_resp.json().get("query_id")
        filters = []
        if query:
            filters.append(f"({query})")
        if tags:
            filters.append(f"tags:({' OR '.join(tags)})")
        if file_types:
            filters.append(f"file_extension:({' OR '.join(file_types)})")
            
        search_string = " AND ".join(filters) if filters else "*"
        
        params = {
            "query_id": query_id,
            "search_string": search_string,
            "page_size": page_size,
        }

        response = await self._client.get("/v1/files", params=params)
        response.raise_for_status()
        data = response.json()

        return SearchResponse(
            results=[self._parse_result(r) for r in data.get("files", [])],
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
        # 1. Upload
        response = await self._client.post("/v1/files", files=files)
        response.raise_for_status()
        try:
            result = response.json() or {}
        except Exception:
            result = {}
        file_id = result.get("id") or result.get("file_id")

        # 2. Add tags if any
        if tags and file_id:
            tag_payload = {"tags": tags}
            tag_resp = await self._client.post(f"/v1/files/{file_id}/tags", json=tag_payload)
            tag_resp.raise_for_status()

        return UploadResult(
            document_id=file_id or filename,
            filename=filename,
            status=result.get("status", "processing"),
        )

    async def chat(
        self,
        question: str,
        document_ids: list[str] | None = None,
    ) -> ChatResponse:
        # 1. Create context
        payload = {"query_id": "chat-context"}
        if document_ids:
            payload["file_ids"] = document_ids
            
        ctx_response = await self._client.post("/v1/ai", json=payload)
        ctx_response.raise_for_status()
        context_id = ctx_response.json()["context_id"]
        
        # 2. Process question
        q_payload = {"question": question}
        q_response = await self._client.post(f"/v1/ai/{context_id}/process_question", json=q_payload)
        q_response.raise_for_status()
        data = q_response.json()

        return ChatResponse(
            answer=data.get("answer", "No answer provided"),
            sources=[self._parse_result(s) for s in data.get("sources", [])],
        )

    async def get_tags(self) -> list[str]:
        response = await self._client.get("/v1/files/tags")
        response.raise_for_status()
        return response.json()

    def _parse_result(self, raw: dict) -> SearchResult:
        return SearchResult(
            id=raw.get("file_id", raw.get("id", "")),
            title=raw.get("name", raw.get("title", "Sans titre")),
            content_preview=raw.get("highlight", {}).get("content", [raw.get("content", "")])[0],
            file_type=raw.get("file_extension", raw.get("file_type", "unknown")),
            tags=raw.get("tags", []),
            score=raw.get("score", 0.0),
            thumbnail_url=raw.get("thumbnail_file_id", raw.get("thumbnail_url")),
        )

    async def download_document(self, document_id: str) -> tuple[bytes, str, str]:
        minio_host = config("FILE_STORAGE__HOST", default="localhost:9000")
        minio_access_key = config("FILE_STORAGE__ACCESS_KEY", default="minioadmin")
        minio_secret_key = config("FILE_STORAGE__SECRET_KEY", default="minioadmin")
        
        endpoint_url = f"http://{minio_host}"
        
        def _get_file_sync():
            s3 = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=minio_access_key,
                aws_secret_access_key=minio_secret_key,
                region_name='us-east-1'
            )
            bucket = "loom-filestorage"
            
            response = s3.get_object(Bucket=bucket, Key=document_id)
            content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            
            filename = f"{document_id}"
            if 'ContentDisposition' in response:
                import re
                cd = response['ContentDisposition']
                m = re.search(r'filename="?([^"]+)"?', cd)
                if m:
                    filename = m.group(1)
            elif 'Metadata' in response and 'filename' in response['Metadata']:
                filename = response['Metadata']['filename']
                
            return content, content_type, filename

        return await sync_to_async(_get_file_sync)()

    async def aclose(self) -> None:
        await self._client.aclose()
