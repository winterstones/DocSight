# Security Audit Trail (Compliance logging)

DocSight logs all document search operations for security, auditability, and regulatory compliance. The audit trail logs who searched for what, when, and how many matching documents were returned.

## 1. Audit Trail Database Model

Search logs are stored in the `SearchAuditLog` database table:

### Table Schema

| Field Name | Data Type | Database Constraints | Purpose |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-incrementing identifier. |
| `user` | `ForeignKey` | `on_delete=models.SET_NULL`, `null=True` | Identifies the operator. If user is deleted, log is preserved. |
| `query` | `TextField` | None | Stores the exact query keywords and tags entered. |
| `results_count`| `IntegerField` | `default=0` | Stores the number of results returned by the search engine. |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of the search execution. |

### Indexing and Meta Configuration

To optimize audit analysis and search history queries, the model defines custom ordering and database indexing:
- **Default Ordering**: Descending chronological (`-created_at`).
- **Composite Database Index**: Index on `["user", "-created_at"]` to accelerate audit history searches filtered by a specific operator.

```python
from django.db import models
from django.conf import settings

class SearchAuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    query = models.TextField()
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"])
        ]

    def __str__(self) -> str:
        return f"{self.user} -> '{self.query}' ({self.results_count} results)"
```

---

## 2. Audit Trail Execution Flow

Auditing is triggered asynchronously or inline within the `DocumentSearchService` lifecycle on every search request:

```python
class DocumentSearchService:
    async def search(self, user: User, request: SearchRequest) -> SearchResponse:
        # 1. Resolve tags and execute search
        response = await self.engine.search(...)

        # 2. Log search execution (asynchronously inserts record)
        await self._log_search(user=user, query=request.query, results_count=response.total)

        return response

    async def _log_search(self, user: User, query: str, results_count: int) -> None:
        """Persists audit logs using Django async ORM."""
        from apps.search.models import SearchAuditLog
        await SearchAuditLog.objects.acreate(
            user=user,
            query=query,
            results_count=results_count,
        )
```

---

## 3. Django Admin Security Configuration

To ensure audit trail integrity and prevent administrative tampering or log falsification, the Django admin portal restricts modification:
- **Write Prevention**: The admin panel blocks the creation (`has_add_permission` returning `False`) or deletion of logs.
- **Read-Only Fields**: All fields are registered as read-only to prevent updates.

### Admin Panel Registration (`apps/search/admin.py`)

```python
from django.contrib import admin
from .models import SearchAuditLog

@admin.register(SearchAuditLog)
class SearchAuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "query", "results_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "query")
    readonly_fields = ("user", "query", "results_count", "created_at")

    def has_add_permission(self, request):
        # Prevent manual creation of logs in the admin interface
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent administrative deletion of compliance logs
        return False
```
