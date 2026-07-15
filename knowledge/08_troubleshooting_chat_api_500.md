# RAG Chat API Crash Troubleshooting

This document traces the resolution of a HTTP 500 internal server error occurring when querying the RAG chat API endpoint (`POST /api/search/chat/`) on the Django backend.

---

## 1. Symptoms

1. Requests from the frontend to `POST /api/search/chat/` (specifically when no documents were selected, resulting in `document_ids: []`) yielded a raw HTML 500 debug template from Django.
2. The React frontend (using TanStack Query `useMutation`) crashed when attempting to parse this HTML response as JSON.
3. Django backend logs printed the following exception:
   `httpx.HTTPStatusError: Server error '500 Internal Server Error' for url 'http://localhost:8001/v1/ai'`
4. Inspecting the `docsight-loom-api-1` container (the underlying AI search service) revealed that the service returned a 500 error due to incorrect internal network configurations (frequent `socket.gaierror: [Errno -2] Name or service not known` errors in the Docker logs).

---

## 2. Root Cause Analysis

The code in `backend/apps/search/api/views.py` invoked `DocumentSearchService` as follows:

```python
response = asyncio.run(
    service.chat(
        user=request.user,
        question=data["question"],
        document_ids=data["document_ids"] or None,
    )
)
```

This service called `LoomSearchEngine.chat()`, which forwarded the query to the `docsight-loom-api-1` container via `httpx`.
Whenever the Loom container failed (returning a 500 error), `httpx` threw an `HTTPStatusError` due to the use of `.raise_for_status()`.

However, this exception **was not caught** in the Django `ChatView` handler. Consequently, the exception bubbled up to the Django REST Framework (DRF) layer, which generated a default HTML 500 response page.

The goal of the Django backend is to always guarantee a stable JSON response structure for the frontend, even if downstream microservices encounter failures.

---

## 3. Solution Applied

To make the system resilient against downstream service failures, we wrapped the service call in a `try...except` block in the Django API view (`ChatView`):

1. **`backend/apps/search/api/views.py` Modification**:
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
       logger.exception("Search engine error during RAG chat")
       return Response(
           {"detail": "The AI service (Loom) is temporarily unavailable or encountered an internal error."},
           status=status.HTTP_502_BAD_GATEWAY
       )
   ```
   *Note*: Returning a `502 Bad Gateway` status is semantically correct here since the Django server, acting as a gateway, received an invalid response from an upstream server (Loom API).

2. **Frontend Handlers**:
   The frontend is configured with an `onError` callback in `useMutation`. It now correctly intercepts the HTTP 502 JSON payload and displays a clean error message in the chat UI.

3. **Resilience Testing**:
   Created `backend/tests/test_chat_view.py` to validate this resilience behavior:
   - A happy path test (`test_chat_view_success`) ensuring normal functioning (using `MockSearchEngine`).
   - An edge-case test (`test_chat_view_returns_502_on_engine_failure`) patching the search engine using `unittest.mock.patch` to throw an exception, verifying that the API returns a structured HTTP 502 Bad Gateway JSON payload rather than crashing.

---

## 4. Conclusion

By catching exceptions from downstream services (Loom), we secured the DocSight API gateway layer. The frontend now handles backend/AI service outages gracefully.
