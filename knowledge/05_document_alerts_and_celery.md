# Document Alerts & Celery Task Architecture

DocSight incorporates a real-time alerting engine using Celery, Redis, and Django Mail. Users can register alerts on specific document tags to receive automated notifications when new matching documents are indexed by Loom.

## 1. Document Alert Database Schema

Alert definitions are mapped via the `DocumentAlert` table (`apps/search/models.py`):

### Schema Details

| Field Name | Data Type | Database Constraints | Purpose |
| :--- | :--- | :--- | :--- |
| `id` | `BigAutoField` | Primary Key | Auto-incrementing identifier. |
| `user` | `ForeignKey` | `on_delete=models.CASCADE` | Maps the alert definition to the subscribing user. |
| `tag` | `ForeignKey` | `on_delete=models.CASCADE` | Maps the alert to a specific document Tag. |
| `is_active` | `BooleanField` | `default=True` | Toggles the active status of the alert subscription. |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp when the alert was configured. |

- **Unique Constraint**: The database enforces a `unique_together = ["user", "tag"]` constraint, preventing a user from subscribing to the same tag multiple times.

```python
class DocumentAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="document_alerts")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="alerts")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "tag"]

    def __str__(self) -> str:
        return f"Alert for {self.user} on tag {self.tag}"
```

---

## 2. Celery Asynchronous Architecture

```
[ Loom Search Engine ]
        |
        | Document Discovered / Uploaded
        v
[ Celery Beat / Poll Loom ]
        |
        | Trigger notify_new_document.delay()
        v
[ Redis Broker ]
        |
        | Pop task from queue
        v
[ Celery Workers ]
        |
        | Fetch Matching User Profiles (allowed_tags filter)
        | Defer redundant columns (.only("user__email", "user__first_name"))
        |
        v
[ Django Mail Engine ] ---> Send email notifications (SMTP)
```

---

## 3. Celery Tasks Implementation

Tasks are defined inside `apps/documents/tasks.py`.

### 3.1. Notification Dispatch Task (`notify_new_document`)

Sends email notifications to all users whose tag boundaries encompass the newly indexed document.

```python
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_new_document(self, document_id: str, title: str, tags: list[str]):
    """
    Finds users scoped to the new document's tags and emails them.
    Includes 3 retries, spaced 60s apart, in case SMTP fails.
    """
    try:
        from apps.authentication.models import UserProfile

        # Query Optimization: Find only users whose allowed_tags overlap with document tags
        # and defer unused fields to optimize query execution time
        matching_profiles = (
            UserProfile.objects
            .filter(allowed_tags__name__in=tags)
            .select_related("user")
            .only("user__email", "user__first_name")
            .distinct()
        )

        for profile in matching_profiles:
            if not profile.user.email:
                continue

            send_mail(
                subject=f"[DocSight] New document indexed: {title}",
                message=(
                    f"Hello {profile.user.first_name},\n\n"
                    f"A new document has been indexed in your authorized tag space:\n"
                    f"  Title: {title}\n"
                    f"  Tags: {', '.join(tags)}\n\n"
                    f"Log in to DocSight to view the document."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.user.email],
                fail_silently=False,
            )

    except Exception as exc:
        # Retry task execution upon exception (SMTP failure, DB lock, etc.)
        raise self.retry(exc=exc)
```

### 3.2. Periodic Polling Task (`poll_loom_new_documents`)

Scheduled via Celery Beat (defaulting to a 5-minute schedule) to pull new documents from Loom, compare them against already processed files in Redis sets, and schedule notifications.

```python
@shared_task
def poll_loom_new_documents():
    """
    Polls the Loom search engine API for newly OCR'd and indexed documents.
    Identifies unprocessed documents and triggers notify_new_document.
    """
    import asyncio
    from apps.search.infrastructure.factories import get_search_engine
    
    # 1. Instantiate the correct search engine client via factory
    engine = get_search_engine()
    
    # 2. Query Loom for recently processed documents
    # (Implementation queries Loom API, cross-references processed IDs in a Redis set, 
    # and calls notify_new_document.delay() for each new document detected).
```
