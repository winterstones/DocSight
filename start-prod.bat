@echo off
echo ========================================================
echo Starting DocSight in PRODUCTION mode
echo ========================================================
echo.
echo Note: This uses docker-compose.yml and docker-compose.prod.yml
echo (Ignoring docker-compose.override.yml)
echo.

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo Initialisation des buckets S3 pour Loom...
timeout /t 5 /nobreak > NUL
docker exec docsight-loom-api-1 python -m common.scripts.init_s3
