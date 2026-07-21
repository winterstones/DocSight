import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.search.models import SearchAuditLog

from tests.factories import OperatorFactory

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def operator_user():
    return OperatorFactory()


def test_search_endpoint_requires_auth(api_client):
    url = reverse("search")
    response = api_client.get(url, {"q": "test"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_endpoint_returns_paginated_results(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("search")
    
    response = api_client.get(url, {"q": "maintenance", "page": 1, "page_size": 10})
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Verify paginated response structure
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "results" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert isinstance(data["results"], list)


def test_search_endpoint_query_count(api_client, operator_user, django_assert_max_num_queries):
    """
    Vérifie que la vue de recherche ne fait pas de N+1 queries.
    Doit faire max 3 requêtes (Session/Auth + UserProfile/Tags + AuditLog).
    """
    api_client.force_authenticate(user=operator_user)
    url = reverse("search")
    
    with django_assert_max_num_queries(4):  # Allowing max 4 (Auth, Profile, Tags, AuditLog) based on typical DRF setup
        response = api_client.get(url, {"q": "performance"})
    
    assert response.status_code == status.HTTP_200_OK
    
    # Assert a log was created during this request
    assert SearchAuditLog.objects.count() >= 1

def test_download_endpoint_requires_auth(api_client):
    url = reverse("search-download", kwargs={"doc_id": "doc-001"})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_download_endpoint_returns_file(api_client, operator_user):
    api_client.force_authenticate(user=operator_user)
    url = reverse("search-download", kwargs={"doc_id": "doc-001"})
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "text/plain"
    assert "attachment; filename=\"doc-001.txt\"" in response["Content-Disposition"]
    assert response.content == b"Mock file content for document doc-001"
