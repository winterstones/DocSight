"""
SEMAINE 3 — Mock pour les tests unitaires

MockSearchEngine retourne des données prévisibles en mémoire.
=> 0 appel réseau, 0 dépendance Loom, < 5ms par test.
"""
from apps.search.domain.interfaces import (
    AbstractSearchEngine,
    ChatResponse,
    SearchResponse,
    SearchResult,
    UploadResult,
)


MOCK_RESULTS = [
    SearchResult(
        id="doc-001",
        title="Rapport de maintenance - Ligne A",
        content_preview="Inspection effectuée le 15 janvier. Anomalie détectée sur...",
        file_type="pdf",
        tags=["maintenance", "ligne-a"],
        score=0.95,
    ),
    SearchResult(
        id="doc-002",
        title="Non-conformité #NC-2024-042",
        content_preview="Écart constaté lors du contrôle qualité. Référence norme ISO...",
        file_type="docx",
        tags=["non-conformite", "qualite"],
        score=0.82,
    ),
]


class MockSearchEngine(AbstractSearchEngine):
    """
    Faux moteur de recherche pour les tests.
    Injecté par la factory en mode DEBUG=True avec USE_MOCK=True.

    Permet de tester toute la logique métier (filtrage par périmètre,
    audit trail, pagination) sans aucune dépendance externe.
    """

    def __init__(self, results: list[SearchResult] | None = None):
        self._results = results or MOCK_RESULTS
        # Enregistrements pour les assertions dans les tests
        self.search_calls:  list[dict] = []
        self.upload_calls:  list[dict] = []
        self.chat_calls:    list[dict] = []

    async def search(self, query, tags=None, file_types=None, page=1, page_size=20) -> SearchResponse:
        self.search_calls.append({"query": query, "tags": tags, "page": page})

        # Simuler un filtrage basique par tag
        results = self._results
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]

        return SearchResponse(
            results=results[:page_size],
            total=len(results),
            query=query,
            page=page,
            page_size=page_size,
        )

    async def upload(self, file_bytes, filename, tags=None) -> UploadResult:
        self.upload_calls.append({"filename": filename, "tags": tags})
        return UploadResult(
            document_id=f"mock-{filename}",
            filename=filename,
            status="indexed",
        )

    async def chat(self, question, document_ids=None) -> ChatResponse:
        self.chat_calls.append({"question": question})
        return ChatResponse(
            answer=f"Réponse mock pour : '{question}'",
            sources=self._results[:1],
        )

    async def get_tags(self) -> list[str]:
        return ["maintenance", "non-conformite", "qualite", "ligne-a"]
