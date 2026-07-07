from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# En dev, désactiver le secure cookie (pas de HTTPS local)
SIMPLE_JWT["AUTH_COOKIE_SECURE"] = False

# Logs SQL pour debug
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.db.backends": {"handlers": ["console"], "level": "DEBUG"},
    },
}
