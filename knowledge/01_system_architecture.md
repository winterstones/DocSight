# DocSight System Architecture

DocSight is a document search and business intelligence platform built on top of the Loom search engine. DocSight adds security, compliance, authentication, role-based access control (RBAC), and alerting layers to Loom's core indexing capabilities.

## 1. Technical Stack

| Layer | Technology | Key Dependencies |
| :--- | :--- | :--- |
| **Backend** | Python 3.12, Django 4.2 | Django REST Framework (DRF), django-guardian, django-decouple |
| **Asynchronous Tasks** | Celery 5.6 | Redis 8.0 (Broker & Backend), PostgreSQL (Database) |
| **Frontend** | React 18, TypeScript, Vite | TanStack Query (v5), TanStack Router, TanStack Table, Axios |
| **Infrastructure** | Docker, Docker Compose | PostgreSQL 16, Redis 7, Elasticsearch (managed by Loom) |

## 2. Platform Boundaries & Responsibilities

```
+------------------------------------------+       +------------------------------------------+
|                 DocSight                 |       |                   Loom                   |
|  (Business Application & Security Layer) |       |     (Search & Extraction Engine)         |
+------------------------------------------+       +------------------------------------------+
|  - HttpOnly Cookie JWT Auth              |       |  - Document OCR & Parsing                |
|  - RBAC (operator/supervisor/admin)     | ----> |  - Full-Text Elasticsearch Indexing       |
|  - Search Scope Validation (User Tags)   |  API  |  - Retrieval-Augmented Generation (RAG)  |
|  - Search Audit Logging (Compliance)     | Calls |  - Automatic Tag Extraction              |
|  - Document Alerts & Celery tasks        |       |  - Raw REST API Endpoints                |
+------------------------------------------+       +------------------------------------------+
```

## 3. Dependency Inversion Principle (DIP)

DocSight's domain logic is fully decoupled from the underlying search engine through abstract interfaces. This enables full offline testing using a mock engine.

### Search Engine Client Factory

- **Production Mode**: Calls `LoomSearchEngine` which makes HTTP requests to Loom REST API endpoints (`/api/search/`, `/api/upload/`, `/api/chat/`, `/api/tags/`).
- **Test Mode**: Triggered by setting `USE_MOCK_ENGINE=True` in settings. Returns `MockSearchEngine` (zero network calls, deterministic in-memory mock data).

### Core DIP Interface Definition (`AbstractSearchEngine`)

```python
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
class ChatResponse:
    answer: str
    sources: list[SearchResult]

class AbstractSearchEngine(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        tags: list[str] | None = None,
        file_types: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResponse:
        """Full-text search across documents."""
        pass

    @abstractmethod
    async def upload(self, file_bytes: bytes, filename: str, tags: list[str] | None = None) -> UploadResult:
        """Upload and index a document."""
        pass

    @abstractmethod
    async def chat(self, question: str, document_ids: list[str] | None = None) -> ChatResponse:
        """RAG chat query against indexed documents."""
        pass

    @abstractmethod
    async def get_tags(self) -> list[str]:
        """Fetch all tags registered on the search engine."""
        pass
```
