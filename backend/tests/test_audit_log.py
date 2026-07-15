import pytest
from apps.search.models import SearchAuditLog
from apps.search.domain.services import DocumentSearchService, SearchRequest
from apps.search.infrastructure.mock_engine import MockSearchEngine

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def search_service():
    engine = MockSearchEngine()
    return DocumentSearchService(engine=engine)


@pytest.mark.asyncio
async def test_search_creates_exactly_one_audit_log(search_service, admin_user):
    initial_count = await SearchAuditLog.objects.acount()
    
    await search_service.search(
        user=admin_user,
        request=SearchRequest(query="maintenance documents"),
    )
    
    final_count = await SearchAuditLog.objects.acount()
    assert final_count == initial_count + 1


@pytest.mark.asyncio
async def test_audit_log_contains_required_fields(search_service, admin_user):
    query_text = "test query fields"
    
    await search_service.search(
        user=admin_user,
        request=SearchRequest(query=query_text),
    )
    
    log = await SearchAuditLog.objects.alatest("created_at")
    
    assert log.user == admin_user
    assert log.query == query_text
    assert log.results_count >= 0
    assert log.created_at is not None
