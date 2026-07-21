# S3 Storage with MinIO and Download Proxy Pattern

Ce document explique les modifications récentes apportées à l'architecture pour supporter pleinement le stockage S3 requis par l'API Loom.

## Problème initial
L'API Loom (`registry.gitlab.com/swiss-armed-forces/cyber-command/cea/loom/api:latest`) utilise par défaut des "buckets" de stockage de type S3 pour enregistrer les fichiers importés et extraire leurs textes pour l'indexation.
Si ces buckets ne sont pas accessibles, Loom renvoie une erreur 500 (Internal Server Error) lors de la route `/v1/files`.

## Solution : MinIO Local
Pour contourner ce problème sans modifier l'image tierce de Loom, nous avons ajouté un conteneur **MinIO** à `docker-compose.yml`.
MinIO agit comme un serveur S3 en local sur le réseau Docker.

### Configuration
1. **MinIO** est aliasé sur le réseau interne avec le nom `s3.loom` ou configuré explicitement dans l'environnement de Loom via les variables `FILE_STORAGE__HOST=minio:9000`, `LAZYBYTES_STORAGE__HOST=minio:9000`, etc.
2. **Broker Celery** : Loom utilise des tâches asynchrones pour l'indexation S3. Nous avons mappé `CELERY_BROKER_HOST` et `CELERY_BACKEND_HOST` sur notre instance Redis (`redis:6379/1` et `redis:6379/0`).

### Initialisation S3
MinIO démarre "vide". Pour que Loom fonctionne, il a besoin de 3 buckets par défaut (`loom-filestorage`, `loom-lazybytes`, `loom-intake`).
Un script d'initialisation Python interne à Loom a été configuré dans les scripts de lancement locaux (`start-hybrid.bat`, `start-dev.bat`, `start-prod.bat`) :
```bash
docker exec docsight-loom-api-1 python -m common.scripts.init_s3
```
Ce script crée les buckets nécessaires à chaque lancement si ces derniers n'existent pas.

## Le pattern "Download Proxy" (Future Implémentation)

Actuellement, tout fonctionne très bien pour la recherche et le Chat RAG car ces processus communiquent **uniquement côté serveur** (Backend <-> Loom <-> MinIO). 
Le navigateur client n'a jamais besoin de parler à MinIO directement.

Cependant, si le projet évolue et que les utilisateurs doivent **télécharger le fichier original** depuis l'interface Web (Frontend), une architecture spécifique sera nécessaire.

### Pourquoi ?
Si le backend Django renvoie une "Presigned URL" S3 générée par Loom, elle pointera vers `http://minio:9000/...`. Le navigateur de l'utilisateur final ne pourra pas résoudre cette URL car `minio` n'est pas exposé publiquement (c'est un nom d'hôte interne à Docker).

### La Solution (Proxy Backend)
Le backend Django doit jouer le rôle de proxy (intermédiaire) pour télécharger le fichier :
1. Le Frontend appelle une route Django, par exemple : `GET /api/search/documents/<id>/download/`.
2. Django vérifie le token JWT et les permissions (RBAC) de l'utilisateur.
3. Django récupère le flux de données (bytes) depuis Loom ou directement depuis MinIO (via la librairie `boto3` ou `minio`).
4. Django stream (via `StreamingHttpResponse` ou `FileResponse`) le fichier original jusqu'au Frontend.

Ainsi, la sécurité est maintenue (les fichiers ne sont jamais exposés publiquement via des URLs S3), et l'utilisateur télécharge le fichier depuis l'URL de votre propre API Backend.
