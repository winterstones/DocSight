@echo off
echo ========================================================
echo Starting DocSight in PRODUCTION mode
echo ========================================================
echo.
echo Note: This uses docker-compose.yml and docker-compose.prod.yml
echo (Ignoring docker-compose.override.yml)
echo.

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
