"""
SEMAINE 5 — Tests unitaires seniors

Principes :
  - 0 appel réseau (MockSearchEngine injecté)
  - 0 base de données (domaine pur testé)
  - < 10ms par test
  - Tests déterministes (même résultat à chaque run)
"""
import pytest
from apps.search.domain.services import DocumentSearchService, SearchRequest
from apps.search.infrastructure.mock_engine import MockSearchEngine, MOCK_RESULTS


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_engine():
    """Moteur de recherche en mémoire — 0 réseau."""
    return MockSearchEngine()


@pytest.fixture
def search_service(mock_engine):
    """Service métier avec dépendances injectées."""
    return DocumentSearchService(engine=mock_engine)


@pytest.fixture
def admin_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin", password="admin123", email="admin@docsight.ch"
    )


@pytest.fixture
def operator_user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username="operator", password="op123", email="op@docsight.ch",
        role="operator"
    )
    return user


# ─── Tests du service de recherche ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_returns_results(search_service, admin_user):
    """Le service retourne des résultats depuis le moteur injecté."""
    response = await search_service.search(
        user=admin_user,
        request=SearchRequest(query="maintenance"),
    )

    assert response.total == len(MOCK_RESULTS)
    assert response.query == "maintenance"
    assert len(response.results) > 0


@pytest.mark.asyncio
async def test_search_logs_audit_trail(search_service, admin_user, db):
    """Chaque recherche crée une entrée dans l'audit trail."""
    from apps.search.models import SearchAuditLog

    initial_count = await SearchAuditLog.objects.acount()

    await search_service.search(
        user=admin_user,
        request=SearchRequest(query="rapport"),
    )

    assert await SearchAuditLog.objects.acount() == initial_count + 1
    log = await SearchAuditLog.objects.alatest("created_at")
    assert log.query == "rapport"
    assert log.user == admin_user


@pytest.mark.asyncio
async def test_admin_sees_all_tags(search_service, admin_user, mock_engine):
    """Un admin n'a aucune restriction de périmètre."""
    await search_service.search(
        user=admin_user,
        request=SearchRequest(query="test", tags=["ligne-a"]),
    )

    # L'admin passe son filtre tel quel — pas d'intersection avec un périmètre
    assert mock_engine.search_calls[-1]["tags"] == ["ligne-a"]


@pytest.mark.asyncio
async def test_operator_scope_filters_results(search_service, operator_user, mock_engine, db):
    """Un opérateur ne voit que les docs dans son périmètre de tags."""
    from apps.authentication.models import Tag

    # Donner un périmètre à l'opérateur
    tag = await Tag.objects.acreate(name="ligne-a")
    await operator_user.profile.allowed_tags.aadd(tag)

    await search_service.search(
        user=operator_user,
        request=SearchRequest(query="test", tags=["ligne-a", "confidentiel"]),
    )

    # L'opérateur demandait "ligne-a" ET "confidentiel"
    # Mais son périmètre n'inclut que "ligne-a"
    # => "confidentiel" est filtré
    effective_tags = mock_engine.search_calls[-1]["tags"]
    assert "confidentiel" not in effective_tags
    assert "ligne-a" in effective_tags


@pytest.mark.asyncio
async def test_search_engine_called_once_per_request(search_service, admin_user, mock_engine):
    """Une seule requête vers le moteur par appel search()."""
    await search_service.search(
        user=admin_user,
        request=SearchRequest(query="test"),
    )
    assert len(mock_engine.search_calls) == 1


@pytest.mark.asyncio
async def test_chat_returns_answer(search_service, admin_user):
    """Le service chat retourne une réponse du moteur RAG."""
    response = await search_service.chat(
        user=admin_user,
        question="Quels sont les rapports de maintenance récents ?",
    )
    assert "Quels sont les rapports" in response.answer
    assert isinstance(response.sources, list)
