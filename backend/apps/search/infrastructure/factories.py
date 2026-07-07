"""
SEMAINE 1 — Pattern Factory

Centralise le choix de l'implémentation concrète selon l'environnement.
Le reste du code appelle get_search_engine() et ne sait jamais
si c'est Loom ou le Mock qui tourne derrière.
"""
from django.conf import settings

from apps.search.domain.interfaces import AbstractSearchEngine


def get_search_engine() -> AbstractSearchEngine:
    """
    Factory : retourne l'implémentation correcte selon l'environnement.

    - Tests (USE_MOCK_ENGINE=True) : MockSearchEngine (0 réseau, déterministe)
    - Production                   : LoomSearchEngine (API REST Loom)

    Demain, si vous remplacez Loom par Elasticsearch natif :
    vous modifiez UNIQUEMENT cette fonction.
    """
    use_mock = getattr(settings, "USE_MOCK_ENGINE", False)

    if use_mock:
        from apps.search.infrastructure.mock_engine import MockSearchEngine
        return MockSearchEngine()

    from apps.search.infrastructure.loom_client import LoomSearchEngine
    return LoomSearchEngine()
