"""
SEMAINE 5 — Tâches Celery asynchrones

Envoi de notifications quand de nouveaux documents
correspondent aux critères d'alerte d'un utilisateur.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_new_document(self, document_id: str, title: str, tags: list[str]):
    """
    Notifie les utilisateurs ayant une alerte sur les tags du document.
    Retry automatique en cas d'échec (max 3 fois, 60s entre chaque).
    """
    try:
        from apps.authentication.models import UserProfile, Tag

        # Trouver les utilisateurs dont le périmètre inclut ces tags
        matching_profiles = (
            UserProfile.objects
            .filter(allowed_tags__name__in=tags)
            .select_related("user")
            .only("user__email", "user__first_name")   # ← defer() : 0 champ inutile
            .distinct()
        )

        for profile in matching_profiles:
            if not profile.user.email:
                continue

            send_mail(
                subject=f"[DocSight] Nouveau document : {title}",
                message=(
                    f"Bonjour {profile.user.first_name},\n\n"
                    f"Un nouveau document a été indexé dans votre périmètre :\n"
                    f"  Titre : {title}\n"
                    f"  Tags  : {', '.join(tags)}\n\n"
                    f"Consultez-le sur DocSight."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[profile.user.email],
                fail_silently=False,
            )

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def poll_loom_new_documents():
    """
    Polling périodique de Loom pour détecter les nouveaux documents.
    Planifié via Celery Beat (toutes les 5 minutes).
    """
    import asyncio
    from apps.search.infrastructure.factories import get_search_engine

    engine = get_search_engine()
    # TODO Semaine 5 : implémenter la logique de polling
    # response = asyncio.run(engine.search(query="*", page=1, page_size=10))
    # Comparer avec les documents déjà vus (Redis set)
    # Pour chaque nouveau → notify_new_document.delay(...)
    pass
