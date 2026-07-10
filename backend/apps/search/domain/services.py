"""
SEMAINE 1 — Logique métier pure

Ce service ne connaît ni Loom, ni Django ORM, ni HTTP.
Il reçoit ses dépendances par injection (DIP).
=> Testable à 100% sans aucun service externe.
"""
from dataclasses import dataclass

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

from .interfaces import AbstractSearchEngine, SearchResponse, ChatResponse

User = get_user_model()


@dataclass
class SearchRequest:
    query: str
    tags: list[str] | None = None
    file_types: list[str] | None = None
    page: int = 1
    page_size: int = 20


class DocumentSearchService:
    """
    Orchestre la recherche avec :
    - Filtrage par périmètre utilisateur (tags autorisés)
    - Audit trail (qui a cherché quoi, quand)
    - Délégation au moteur de recherche injecté
    """

    def __init__(self, engine: AbstractSearchEngine):
        self.engine = engine

    async def search(self, user: User, request: SearchRequest) -> SearchResponse:
        # 1. Appliquer le périmètre utilisateur
        allowed_tags = await self._get_allowed_tags(user)
        effective_tags = self._intersect_tags(request.tags, allowed_tags)

        # 2. Déléguer au moteur (Loom ou Mock)
        response = await self.engine.search(
            query=request.query,
            tags=effective_tags,
            file_types=request.file_types,
            page=request.page,
            page_size=request.page_size,
        )

        # 3. Audit trail (sera implémenté en semaine 4)
        await self._log_search(user=user, query=request.query, results_count=response.total)

        return response

    async def chat(self, user: User, question: str, document_ids: list[str] | None = None) -> ChatResponse:
        """RAG : question sur les documents autorisés pour cet utilisateur."""
        return await self.engine.chat(question=question, document_ids=document_ids)

    @sync_to_async
    def _get_allowed_tags(self, user: User) -> list[str] | None:
        """
        Retourne les tags autorisés selon le profil utilisateur.
        None = accès total (admin).
        """
        if user.is_superuser:
            return None
        try:
            return list(user.profile.allowed_tags.values_list("name", flat=True))
        except AttributeError:
            return []

    def _intersect_tags(
        self,
        requested: list[str] | None,
        allowed: list[str] | None,
    ) -> list[str] | None:
        if allowed is None:
            return requested  # Admin : pas de restriction
        if not requested:
            return allowed    # Aucun filtre demandé : périmètre utilisateur complet
        return list(set(requested) & set(allowed))  # Intersection

    async def _log_search(self, user: User, query: str, results_count: int) -> None:
        """Audit trail — persisté en DB (implémentation Semaine 4)."""
        from apps.search.models import SearchAuditLog
        await SearchAuditLog.objects.acreate(
            user=user,
            query=query,
            results_count=results_count,
        )
