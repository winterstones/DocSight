from .base import *  # noqa

DEBUG = False

# Autoriser l'accès depuis n'importe quel hôte ou depuis ceux définis dans l'environnement
import os
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Sécurité des cookies en prod (HTTPS)
SIMPLE_JWT["AUTH_COOKIE_SECURE"] = True

# Configuration CORS pour la prod
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
# Si CORS_ALLOWED_ORIGINS est vide, l'application frontend doit être servie
# sur le même domaine, ou bien configurer la variable d'environnement.
