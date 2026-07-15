@echo off
echo ========================================================
echo Starting DocSight in HYBRID LOCAL mode
echo ========================================================
echo.

if not exist "backend\.venv\Scripts\activate.bat" (
    echo [1/3] Creation de l'environnement virtuel Python...
    cd backend
    python -m venv venv
    call .\.venv\Scripts\activate.bat
    echo Installation des dependances Python...
    pip install -r requirements/base.txt -r requirements/development.txt
    cd ..
    echo.
)

if not exist "frontend\node_modules" (
    echo [2/3] Installation des dependances Node...
    cd frontend
    call npm install
    cd ..
    echo.
)

echo [3/3] Demarrage des services...
echo Lancement de l'infrastructure Docker (Postgres, Redis, MinIO, Loom, ES)...
docker-compose up -d postgres redis elasticsearch minio loom-api

echo Initialisation des buckets S3 pour Loom...
timeout /t 5 /nobreak > NUL
docker exec docsight-loom-api-1 python -m common.scripts.init_s3

echo.
echo Lancement du Backend Django...
start "Django Backend" cmd /k "cd backend && call .\.venv\Scripts\activate.bat && python manage.py runserver"

echo Lancement du Worker Celery...
start "Celery Worker" cmd /k "cd backend && call .\.venv\Scripts\activate.bat && celery -A config worker -l info -P solo"

echo Lancement du Frontend Vite...
start "Vite Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Tout est lance ! Vous pouvez fermer cette fenetre, les autres fenetres
echo contiennent les logs de votre backend, celery et frontend.
