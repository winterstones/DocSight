import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.search.infrastructure.mock_engine import MockSearchEngine

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username="testuser_chat", password="password123")

@pytest.mark.django_db
def test_chat_view_success(api_client, user):
    """
    Vérifie que le point d'accès /api/search/chat/ fonctionne correctement
    avec le mock engine par défaut, renvoyant answer et sources.
    """
    api_client.force_authenticate(user=user)
    
    url = reverse("search-chat")
    
    with patch("apps.search.api.views.get_search_engine") as mock_get_engine:
        mock_get_engine.return_value = MockSearchEngine()
        response = api_client.post(url, {"question": "Test", "document_ids": []}, format="json")
    
    assert response.status_code == 200
    assert "answer" in response.data
    assert "sources" in response.data

@pytest.mark.django_db
def test_chat_view_returns_502_on_engine_failure(api_client, user):
    """
    Vérifie que l'API intercepte correctement un crash du moteur de recherche
    (ex: Loom inaccessible) et renvoie un 502 JSON propre au lieu d'une page 500 HTML.
    """
    api_client.force_authenticate(user=user)
    
    url = reverse("search-chat")
    
    # On mock le moteur retourné par get_search_engine
    with patch("apps.search.api.views.get_search_engine") as mock_get_engine:
        mock_engine_instance = MagicMock()
        mock_engine_instance.chat.side_effect = Exception("Loom is dead")
        mock_get_engine.return_value = mock_engine_instance
        
        response = api_client.post(url, {"question": "Test", "document_ids": []}, format="json")
        
    assert response.status_code == 502
    assert "detail" in response.data
    assert "indisponible" in response.data["detail"]
