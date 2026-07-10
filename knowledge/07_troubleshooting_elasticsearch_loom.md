# Résolution du problème d'intégration Elasticsearch / Loom API

Ce document trace la résolution d'une erreur 500 persistante lors de l'appel à l'API de recherche Django (`/api/search/`), qui communique avec l'API Loom.

## Symptômes

1. Appels à `GET /api/search/?q=test` sur le backend Django retournaient une erreur HTTP 500 (`HTTPStatusError`).
2. Dans les logs du backend Django, l'erreur détaillée indiquait que l'appel vers l'API Loom (`http://localhost:8001/v1/files`) renvoyait une erreur `400 Bad Request`.
3. Côté Loom API et Elasticsearch, selon la version d'Elasticsearch utilisée, l'erreur variait :
   - Sur Elasticsearch `9.2.1` (version par défaut) : `java.io.IOException: Invalid vInt` lors de la recherche.
   - Sur Elasticsearch `8.17.0` (tentative de downgrade) : `BadRequestError(400, 'None')` lors de l'initialisation des index avec `init_elasticsearch`.

## Analyse de la cause racine (Root Cause)

Le problème ne venait pas d'une corruption de l'index ou d'une incompatibilité majeure de la version Elasticsearch, mais d'une erreur d'utilisation de l'API REST Loom depuis le backend Django.

Dans `backend/apps/search/infrastructure/loom_client.py` (l'implémentation de `AbstractSearchEngine`), la méthode `search()` générait un faux `query_id` sous la forme d'un UUID aléatoire :

```python
import uuid
query_id = str(uuid.uuid4())
```

Ce `query_id` était ensuite envoyé à l'API Loom via la requête `GET /v1/files?query_id=<uuid>`. 

Cependant, dans l'API Loom, le paramètre `query_id` est utilisé pour stocker et transmettre le **Point In Time (PIT) ID** d'Elasticsearch. Un PIT ID est une chaîne encodée en base64 contenant l'état interne de la recherche (dont des entiers variables de Lucene - `vInt`). Lorsque Elasticsearch tentait de décoder l'UUID aléatoire envoyé par Django comme s'il s'agissait d'un PIT ID valide, il levait l'erreur de parsing `Invalid vInt`.

## Solution appliquée

La solution consistait à corriger le client Django (`loom_client.py`) pour qu'il respecte le flux correct de l'API Loom. Au lieu de générer un UUID aléatoire, le client doit d'abord interroger l'API Loom pour obtenir un vrai PIT ID :

1. **Modification de `loom_client.py`** :
   Ajout d'une étape pour récupérer un `query_id` valide avant d'effectuer la recherche.
   
   ```python
   # Obtenir un Point In Time (PIT) ID valide auprès de l'API Loom
   query_resp = await self._client.post("/v1/files/query")
   query_resp.raise_for_status()
   query_id = query_resp.json().get("query_id")
   ```

2. **Restauration de la version Elasticsearch** :
   Nous sommes revenus à l'image `docker.elastic.co/elasticsearch/elasticsearch:9.2.1` dans `docker-compose.yml`, qui est la version parfaitement compatible avec le client Python utilisé par l'API Loom.

3. **Réinitialisation de l'index** :
   Après la restauration, le volume Elasticsearch a été recréé et le script d'initialisation a été relancé avec succès (`docker exec docsight-loom-api-1 python -m common.scripts.init_elasticsearch`).

## Conclusion

L'API de recherche backend fonctionne désormais correctement et renvoie le format attendu (HTTP 200). Le frontend peut maintenant consommer la route `/api/search/` avec son token JWT (ou cookie de session) sans encombre.
