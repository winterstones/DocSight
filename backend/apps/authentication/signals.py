from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un UserProfile à la création de l'utilisateur."""
    if created:
        from apps.authentication.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)
