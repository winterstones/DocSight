@echo off
echo ========================================================
echo Starting DocSight in DEVELOPMENT mode
echo ========================================================
echo.
echo Note: This uses docker-compose.yml and docker-compose.override.yml
echo.

docker-compose up -d --build

echo Initialisation des buckets S3 pour Loom...
timeout /t 5 /nobreak > NUL
docker exec docsight-loom-api-1 python -m common.scripts.init_s3

echo Attachement aux logs...
docker-compose logs -f
