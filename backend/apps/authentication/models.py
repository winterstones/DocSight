from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Utilisateur étendu avec rôle et périmètre documentaire."""

    class Role(models.TextChoices):
        OPERATOR  = "operator",  "Opérateur"
        SUPERVISOR = "supervisor", "Superviseur"
        ADMIN     = "admin",     "Administrateur"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self) -> str:
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    """
    Périmètre documentaire par utilisateur.
    allowed_tags = None (admin) → accès total
    allowed_tags = ["ligne-a"] → voit uniquement les docs tagués "ligne-a"
    """
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    allowed_tags = models.ManyToManyField("Tag", blank=True)

    def __str__(self) -> str:
        return f"Profil de {self.user.username}"


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name
