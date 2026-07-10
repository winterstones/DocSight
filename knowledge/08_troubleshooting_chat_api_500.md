# Résolution du plantage de l'API RAG (Loom API)

Ce document trace la résolution d'une erreur 500 survenant lors de l'appel au endpoint RAG (`POST /api/search/chat/`) de l'API Django.

## Symptômes

1. Les appels du frontend vers l'API backend `POST /api/search/chat/` (notamment lorsqu'aucun document n'était sélectionné avec `document_ids: []`) se soldaient par une erreur HTTP 500 brute renvoyée par Django.
2. Le frontend React (utilisant TanStack Query via `useMutation`) plantait en essayant de parser cette réponse qui était en fait une page de debug HTML Django.
3. Les logs du backend Django indiquaient l'erreur suivante :
   `httpx.HTTPStatusError: Server error '500 Internal Server Error' for url 'http://localhost:8001/v1/ai'`
4. Du côté du conteneur `docsight-loom-api-1` (l'API d'IA sous-jacente), il s'est avéré que ce service retournait une erreur interne (500) à cause d'une configuration réseau incorrecte (des erreurs récurrentes `socket.gaierror: [Errno -2] Name or service not known` étaient visibles dans les logs du conteneur Docker).

## Analyse de la cause racine (Root Cause)

Le code dans `backend/apps/search/api/views.py` appelait le `DocumentSearchService` de la façon suivante :

```python
response = asyncio.run(
    service.chat(
        user=request.user,
        question=data["question"],
        document_ids=data["document_ids"] or None,
    )
)
```

Ce service faisait appel à `LoomSearchEngine.chat()`, qui transmettait la requête au conteneur `docsight-loom-api-1` via la librairie `httpx`.
Lorsque le conteneur Loom plantait (en renvoyant un 500 Internal Server Error), `httpx` levait automatiquement une exception `HTTPStatusError` grâce à l'appel de `.raise_for_status()`. 

Cependant, cette exception **n'était pas interceptée** dans la vue Django (`ChatView`), ce qui faisait planter tout le traitement de la requête au niveau de Django REST Framework (DRF), générant ainsi un traceback HTML 500.

L'objectif du backend Django est de toujours garantir une réponse stable et au format JSON pour le frontend, même si un microservice externe tombe en panne.

## Solution appliquée

Pour rendre le système robuste ("resilient") vis-à-vis des pannes du moteur de recherche externe, nous avons encapsulé l'appel dans un bloc `try...except` dans le contrôleur de l'API (`ChatView`).

1. **Modification de `backend/apps/search/api/views.py`** :
   ```python
   try:
       response = asyncio.run(
           service.chat(
               user=request.user,
               question=data["question"],
               document_ids=data["document_ids"] or None,
           )
       )
       return Response(ChatResponseSerializer(response).data)
   except Exception as e:
       logger.exception("Erreur du moteur de recherche lors du chat RAG")
       return Response(
           {"detail": "Le service d'IA (Loom) est temporairement indisponible ou a rencontré une erreur interne."},
           status=status.HTTP_502_BAD_GATEWAY
       )
   ```
   *Note*: L'utilisation du code HTTP `502 Bad Gateway` est sémantiquement correcte ici, car Django agit comme une passerelle qui reçoit une réponse invalide ou une erreur d'un serveur tiers (Loom API).

2. **Garantie Front-End** :
   Le frontend étant déjà configuré avec le callback `onError` dans `useMutation`, il intercepte désormais proprement l'erreur HTTP 502 (dont le format est bien en JSON) et affiche un message d'erreur approprié dans l'interface de messagerie.

3. **Mise en place de tests de robustesse** :
   Création du fichier `backend/tests/test_chat_view.py` pour valider ce comportement :
   - Un test "happy path" `test_chat_view_success` vérifiant le fonctionnement normal (simulé avec le `MockSearchEngine`).
   - Un test "edge case" `test_chat_view_returns_502_on_engine_failure` simulant explicitement une exception au niveau du moteur de recherche via un mock Python (`unittest.mock.patch`), afin de garantir que l'API renvoie bien un `502 Bad Gateway` au format JSON et non un crash HTML.

## Conclusion

En capturant correctement les exceptions de communication avec le microservice tiers (Loom), nous avons rendu la couche API de DocSight beaucoup plus robuste. Le frontend peut maintenant gérer ces indisponibilités temporaires avec élégance, sans crasher.
