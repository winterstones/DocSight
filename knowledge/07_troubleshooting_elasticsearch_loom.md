# Elasticsearch / Loom API Integration Troubleshooting

This document traces the resolution of a persistent 500 error encountered when calling the Django search API (`/api/search/`), which communicates with the Loom API.

---

## 1. Symptoms

1. Requests to `GET /api/search/?q=test` on the Django backend returned a 500 HTTP response status (`HTTPStatusError`).
2. Detailed errors in the Django backend logs indicated that the call to the Loom API (`http://localhost:8001/v1/files`) was failing with a `400 Bad Request` status.
3. On the Loom API and Elasticsearch side, the error message varied depending on the Elasticsearch version:
   - **Elasticsearch `9.2.1`** (default version): `java.io.IOException: Invalid vInt` during searches.
   - **Elasticsearch `8.17.0`** (downgrade attempt): `BadRequestError(400, 'None')` during index initialization via `init_elasticsearch`.

---

## 2. Root Cause Analysis

The issue was not caused by index corruption or major version incompatibilities, but rather by an incorrect usage of the Loom REST API within the Django backend.

In `backend/apps/search/infrastructure/loom_client.py` (the `AbstractSearchEngine` implementation), the `search()` method generated a mock `query_id` using a random UUID:

```python
import uuid
query_id = str(uuid.uuid4())
```

This `query_id` was subsequently forwarded to the Loom API in the request: `GET /v1/files?query_id=<uuid>`.

However, the Loom API utilizes the `query_id` parameter to store and transmit the Elasticsearch **Point In Time (PIT) ID**. A PIT ID is a base64-encoded string representing the internal state of a search context (which includes variable-length integers - `vInt` in Lucene). When Elasticsearch attempted to decode the random UUID string as if it were a valid base64 PIT ID, it threw the Lucene/Elasticsearch parsing exception: `Invalid vInt`.

---

## 3. Solution Applied

The resolution required correcting the Django client (`loom_client.py`) to respect the proper Loom API request lifecycle. Instead of generating a random UUID, the client must first fetch a valid PIT ID from the Loom API:

1. **`loom_client.py` Modification**:
   Added a step to retrieve a valid `query_id` before performing the actual search:
   
   ```python
   # Fetch a valid Point In Time (PIT) ID from the Loom API
   query_resp = await self._client.post("/v1/files/query")
   query_resp.raise_for_status()
   query_id = query_resp.json().get("query_id")
   ```

2. **Restoring Elasticsearch Image**:
   Restored the image to `docker.elastic.co/elasticsearch/elasticsearch:9.2.1` in `docker-compose.yml`, which is fully compatible with the Python client used by the Loom API.

3. **Re-initializing the Index**:
   Re-created the Elasticsearch Docker volume and successfully executed the index initialization script:
   ```bash
   docker exec docsight-loom-api-1 python -m common.scripts.init_elasticsearch
   ```

---

## 4. Conclusion

The backend search API is now operational and returns a valid HTTP 200 response. The React frontend can seamlessly query the `/api/search/` endpoint using its HttpOnly JWT session cookie.
