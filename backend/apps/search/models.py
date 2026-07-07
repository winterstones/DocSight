from django.db import models
from django.conf import settings
from apps.authentication.models import Tag


class SearchAuditLog(models.Model):
    """
    Trace chaque recherche : qui a cherché quoi, quand.
    Requis pour compliance et sécurité dans les environnements industriels.
    """
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    query        = models.TextField()
    results_count = models.IntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes  = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.user} → '{self.query}' ({self.results_count} résultats)"


class DocumentAlert(models.Model):
    """
    Alerte définie par un utilisateur sur un tag spécifique.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="document_alerts")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="alerts")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["user", "tag"]

    def __str__(self) -> str:
        return f"Alerte de {self.user} sur le tag {self.tag}"
