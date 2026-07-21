import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Active le mock engine pour tous les tests — 0 dépendance Loom
os.environ["USE_MOCK_ENGINE"] = "True"
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


def pytest_configure(config):
    from django.conf import settings
    if not settings.configured:
        django.setup()

import pytest
@pytest.fixture(autouse=True)
def enable_mock_engine(settings):
    settings.USE_MOCK_ENGINE = True

