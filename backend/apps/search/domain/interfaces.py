"""
SEMAINE 1 — DIP : Le cœur de l'architecture DocSight

Ces interfaces définissent les CONTRATS que l'infrastructure doit respecter.
Le domaine métier ne connaît jamais LoomSearchEngine ou MockSearchEngine
— il ne parle qu'à AbstractSearchEngine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    id: str
    title: str
    content_preview: str
    file_type: str
    tags: list[str] = field(default_factory=list)
    score: float = 0.0
    thumbnail_url: str | None = None


@dataclass
class SearchResponse:
    results: list[SearchResult]
    total: int
    query: str
    page: int
    page_size: int


@dataclass
class UploadResult:
    document_id: str
    filename: str
    status: str  # "indexed" | "processing" | "error"


@dataclass
class ChatMessage:
    role: str   # "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    answer: str
    sources: list[SearchResult]


class AbstractSearchEngine(ABC):
    """
    Contrat strict que toute implémentation de moteur de recherche doit respecter.
    Loom, Elasticsearch, MockEngine — tous doivent s'y plier.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        tags: list[str] | None = None,
        file_types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """Recherche full-text dans les documents indexés."""
        pass

    @abstractmethod
    async def upload(self, file_bytes: bytes, filename: str, tags: list[str] | None = None) -> UploadResult:
        """Upload et indexation d'un document."""
        pass

    @abstractmethod
    async def chat(self, question: str, document_ids: list[str] | None = None) -> ChatResponse:
        """RAG : question sur les documents indexés."""
        pass

    @abstractmethod
    async def get_tags(self) -> list[str]:
        """Récupère tous les tags disponibles."""
        pass

    @abstractmethod
    async def download_document(self, document_id: str) -> tuple[bytes, str, str]:
        """Télécharge le fichier original. Retourne (contenu, content_type, filename)."""
        pass
