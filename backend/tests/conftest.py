import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Active le mock engine pour tous les tests — 0 dépendance Loom
os.environ["USE_MOCK_ENGINE"] = "True"


def pytest_configure(config):
    from django.conf import settings
    if not settings.configured:
        django.setup()
