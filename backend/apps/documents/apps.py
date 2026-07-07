"""
App documents — Semaine 5

Gère les notifications Celery quand de nouveaux documents
sont indexés dans Loom (webhook ou polling).
"""
from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name               = "apps.documents"
    verbose_name       = "Documents"
