# DocSight 🔍

> Application métier de recherche documentaire construite sur [Loom](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom) — le moteur de recherche open-source du Cyber Command Suisse.

[![CI](https://github.com/YOUR_USERNAME/docsight/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/docsight/actions)

## Concept

Loom fournit l'infrastructure (OCR, indexation Elasticsearch, RAG chatbot).
DocSight ajoute la **couche applicative métier** :

| Ce que Loom fournit | Ce que DocSight ajoute |
|---|---|
| Moteur de recherche full-text | Authentification JWT (HttpOnly cookies) |
| OCR et extraction de contenu | Rôles : Opérateur / Superviseur / Admin |
| RAG chatbot | Périmètre documentaire par utilisateur |
| API REST | Audit trail (qui cherche quoi, quand) |
| Tags automatiques | Alertes sur nouveaux documents (Celery) |

## Stack Technique

```
Backend  : Django 4.2 + DRF + Celery + Redis + PostgreSQL
Frontend : React 18 + TanStack Query + TanStack Router + TanStack Table
Validation: Zod (frontend) + DRF Serializers (backend)
Auth     : JWT Double Token via HttpOnly Cookies
Tests    : pytest + Vitest + MSW
Infra    : Docker Compose + GitHub Actions CI/CD
```

## Architecture Backend

```
apps/search/
├── domain/
│   ├── interfaces.py   # AbstractSearchEngine (DIP — Dependency Inversion)
│   └── services.py     # Logique métier pure, 0 dépendance externe
├── infrastructure/
│   ├── loom_client.py  # Implémentation Loom (production)
│   ├── mock_engine.py  # Implémentation mock (tests — 0 réseau)
│   └── factories.py    # Sélection automatique selon l'environnement
└── api/
    ├── serializers.py  # Validation DRF
    └── views.py        # Routing HTTP → service
```

## Démarrage rapide

### Prérequis
```bash
git clone https://github.com/YOUR_USERNAME/docsight.git
cd docsight
cp .env.example .env # N'oubliez pas d'éditer les variables si besoin
```

Pour vous faciliter la vie sous Windows, des scripts de lancement sont fournis à la racine du projet :

### Option 1 : Développement Hybride (Recommandé)
Laisse Docker s'occuper de l'infrastructure lourde, mais fait tourner votre code en local pour le hot-reload et le débogage.
1. Exécutez `start-hybrid.bat`
2. Le script lancera automatiquement les bases de données via Docker et ouvrira 3 terminaux (Django, Celery, React).

### Option 2 : Développement Full Docker
Exécute tout l'environnement dans Docker.
1. Exécutez `start-dev.bat`

### Initialisation & Utilisateurs de démo
Lors du premier lancement, vous devez initialiser la base de données :
```bash
# Si vous utilisez le mode hybride :
cd backend
python manage.py migrate
python manage.py create_demo_users

# Si vous utilisez le mode Full Docker :
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py create_demo_users
```

### Accès à l'application
- **Frontend** : http://localhost:5173
- **Backend API** : http://localhost:8000/api/
- **Admin Django** : http://localhost:8000/admin/
- **Loom API** : http://localhost:8001

### Option 3 : Production
Pour simuler l'environnement de production (Nginx, Gunicorn) :
1. Exécutez `start-prod.bat`

## Tests

```bash
# Backend — pytest avec coverage
cd backend
pytest tests/ -v --cov=apps

# Frontend — vitest
cd frontend
npm test
```

## Principes d'architecture

### Dependency Inversion (SOLID — D)

```python
# Le service ne connaît pas Loom — il parle à une interface abstraite
class DocumentSearchService:
    def __init__(self, engine: AbstractSearchEngine):
        self.engine = engine  # Injecté : LoomSearchEngine ou MockSearchEngine

# En production
service = DocumentSearchService(engine=LoomSearchEngine())

# En tests — 0 réseau, < 5ms
service = DocumentSearchService(engine=MockSearchEngine())
```

### JWT Double Token via HttpOnly Cookies

```
Login → Django pose access_token (15min) + refresh_token (7j) en HttpOnly
React → withCredentials: true → cookies envoyés automatiquement
401   → Axios intercepteur → POST /auth/refresh/ → nouveau access_token
XSS   → Impossible de voler les tokens (JavaScript ne peut pas lire HttpOnly)
```

## Contribuer à Loom

Ce projet est construit sur Loom. Si vous trouvez un bug ou une amélioration possible dans Loom pendant le développement de DocSight, consultez les [guidelines de contribution](https://gitlab.com/swiss-armed-forces/cyber-command/cea/loom/-/blob/main/CONTRIBUTING.md).

## Licence

MIT
