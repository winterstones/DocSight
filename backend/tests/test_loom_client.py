import pytest
from unittest.mock import patch, MagicMock
from apps.search.infrastructure.loom_client import LoomSearchEngine

@pytest.mark.asyncio
async def test_loom_search_engine_fetches_query_id():
    """
    Test que LoomSearchEngine appelle bien POST /v1/files/query 
    pour récupérer un vrai query_id (PIT ID) avant d'appeler GET /v1/files.
    Ceci garantit qu'on n'envoie pas un simple UUID aléatoire qui ferait 
    planter Elasticsearch (erreur Invalid vInt).
    """
    engine = LoomSearchEngine(base_url="http://fake-loom")

    # Mocker la réponse du POST (génération du PIT ID)
    mock_post_resp = MagicMock()
    mock_post_resp.json.return_value = {"query_id": "valid-pit-id-123"}
    
    # Mocker la réponse du GET (résultats de recherche)
    mock_get_resp = MagicMock()
    mock_get_resp.json.return_value = {"files": [], "total": 0}

    async def mock_post(url, *args, **kwargs):
        if url == "/v1/files/query":
            return mock_post_resp
        raise ValueError(f"Unexpected POST url: {url}")

    async def mock_get(url, *args, **kwargs):
        if url == "/v1/files":
            return mock_get_resp
        raise ValueError(f"Unexpected GET url: {url}")

    with patch.object(engine._client, "post", side_effect=mock_post) as mock_post_method, \
         patch.object(engine._client, "get", side_effect=mock_get) as mock_get_method:

        response = await engine.search(query="test")

        # 1. Vérifier que POST /v1/files/query a bien été appelé
        mock_post_method.assert_called_once_with("/v1/files/query")

        # 2. Vérifier que GET /v1/files a bien été appelé
        mock_get_method.assert_called_once()
        
        # 3. Vérifier que le paramètre query_id passé au GET correspond au retour du POST
        call_kwargs = mock_get_method.call_args[1]
        assert "params" in call_kwargs
        assert call_kwargs["params"]["query_id"] == "valid-pit-id-123"
        
        # 4. Vérifier que la recherche elle-même a retourné une SearchResponse correcte
        assert response.total == 0
        assert response.query == "test"
