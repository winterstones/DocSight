import asyncio

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser

from apps.search.domain.services import DocumentSearchService, SearchRequest
from apps.search.infrastructure.factories import get_search_engine
from .serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
)


def _get_service() -> DocumentSearchService:
    """Instancie le service avec le moteur sélectionné par la factory."""
    return DocumentSearchService(engine=get_search_engine())


class SearchView(APIView):
    """
    GET /api/search/?q=maintenance&tags=ligne-a&page=1

    - Filtre automatiquement par périmètre utilisateur
    - Journalise dans l'audit trail
    - Utilise only() côté Loom pour les champs de liste
    """

    def get(self, request):
        serializer = SearchRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service  = _get_service()
        response = asyncio.run(
            service.search(
                user=request.user,
                request=SearchRequest(
                    query=data["q"],
                    tags=data["tags"] or None,
                    file_types=data["file_types"] or None,
                    page=data["page"],
                    page_size=data["page_size"],
                ),
            )
        )

        return Response(SearchResponseSerializer(response).data)


class ChatView(APIView):
    """POST /api/search/chat/ — RAG : question sur les documents indexés."""

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service  = _get_service()
        response = asyncio.run(
            service.chat(
                user=request.user,
                question=data["question"],
                document_ids=data["document_ids"] or None,
            )
        )

        return Response(ChatResponseSerializer(response).data)


class TagsView(APIView):
    """GET /api/search/tags/ — Liste des tags disponibles."""

    def get(self, request):
        engine = get_search_engine()
        tags   = asyncio.run(engine.get_tags())
        return Response({"tags": tags})


class UploadView(APIView):
    """POST /api/search/upload/ — Upload et indexation d'un document."""
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Aucun fichier fourni."}, status=status.HTTP_400_BAD_REQUEST)

        tags   = request.data.getlist("tags", [])
        engine = get_search_engine()
        result = asyncio.run(
            engine.upload(
                file_bytes=file.read(),
                filename=file.name,
                tags=tags or None,
            )
        )

        return Response({"document_id": result.document_id, "status": result.status})
